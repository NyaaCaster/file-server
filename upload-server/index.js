const express = require('express');
const multer = require('multer');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: process.env.API_KEYS_FILE || '/app/config/api-keys.env' });

const app = express();
const PORT = process.env.PORT || 8080;
const UPLOAD_DIR = process.env.UPLOAD_DIR || '/usr/share/nginx/html/files';
const FILE_SERVER_BASE_URL = process.env.FILE_SERVER_BASE_URL || '/files';
const API_KEY = process.env.API_KEY || 'test-api-key-for-testing';

if (process.env.NODE_ENV !== 'test' && !process.env.API_KEY) {
    console.error('[Error] API_KEY not set. Please configure api-keys.env');
    process.exit(1);
}

if (process.env.NODE_ENV !== 'test') {
    console.log(`[Auth] API Key loaded (${API_KEY.length} characters)`);
}

function authMiddleware(req, res, next) {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ 
            success: false, 
            error: 'Missing Authorization header. Use: Authorization: Bearer YOUR_API_KEY' 
        });
    }
    
    const key = authHeader.substring(7);
    
    if (key !== API_KEY) {
        return res.status(401).json({ 
            success: false, 
            error: 'Invalid API key' 
        });
    }
    
    next();
}

const getCategory = (req) => {
    return req.headers['x-upload-category'] || 
           req.query.category || 
           req.body.category || 
           'general';
};

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const subDir = getCategory(req);
        const uploadPath = path.join(UPLOAD_DIR, subDir);
        fs.mkdirSync(uploadPath, { recursive: true });
        cb(null, uploadPath);
    },
    filename: (req, file, cb) => {
        const originalName = Buffer.from(file.originalname, 'latin1').toString('utf8');
        cb(null, originalName);
    }
});

const fileFilter = (req, file, cb) => {
    const blockedTypes = [
        'application/x-executable',
        'application/x-msdos-program',
        'application/x-msdownload'
    ];
    
    if (blockedTypes.includes(file.mimetype)) {
        cb(new Error(`Blocked file type: ${file.mimetype}`), false);
    } else {
        cb(null, true);
    }
};

const upload = multer({
    storage,
    fileFilter,
    limits: {
        fileSize: 50 * 1024 * 1024
    }
});

app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.post('/api/upload', authMiddleware, upload.single('file'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ 
            success: false, 
            error: 'No file provided' 
        });
    }
    
    const subDir = getCategory(req);
    const relativePath = `${subDir}/${req.file.filename}`;
    const fileUrl = `${FILE_SERVER_BASE_URL}/${relativePath}`;
    
    console.log(`[Upload] ${req.file.originalname} -> ${fileUrl}`);
    
    res.json({
        success: true,
        filename: req.file.filename,
        originalName: Buffer.from(req.file.originalname, 'latin1').toString('utf8'),
        size: req.file.size,
        mimeType: req.file.mimetype,
        path: relativePath,
        url: fileUrl
    });
});

app.post('/api/upload/multiple', authMiddleware, upload.array('files', 20), (req, res) => {
    if (!req.files || req.files.length === 0) {
        return res.status(400).json({ 
            success: false, 
            error: 'No files provided' 
        });
    }
    
    const subDir = getCategory(req);
    const files = req.files.map(file => {
        const relativePath = `${subDir}/${file.filename}`;
        return {
            filename: file.filename,
            originalName: Buffer.from(file.originalname, 'latin1').toString('utf8'),
            size: file.size,
            mimeType: file.mimetype,
            path: relativePath,
            url: `${FILE_SERVER_BASE_URL}/${relativePath}`
        };
    });
    
    console.log(`[Upload] ${files.length} files uploaded`);
    
    res.json({
        success: true,
        count: files.length,
        files
    });
});

app.post('/api/delete', authMiddleware, (req, res) => {
    const { path: filePath } = req.body;
    
    if (!filePath) {
        return res.status(400).json({ 
            success: false, 
            error: 'Missing file path' 
        });
    }
    
    const fullPath = path.join(UPLOAD_DIR, filePath);
    
    if (!path.resolve(fullPath).startsWith(path.resolve(UPLOAD_DIR))) {
        return res.status(403).json({ 
            success: false, 
            error: 'Invalid path' 
        });
    }
    
    fs.unlink(fullPath, (err) => {
        if (err) {
            if (err.code === 'ENOENT') {
                return res.status(404).json({ 
                    success: false, 
                    error: 'File not found' 
                });
            }
            return res.status(500).json({ 
                success: false, 
                error: `Delete failed: ${err.message}` 
            });
        }
        
        console.log(`[Delete] ${filePath}`);
        res.json({ success: true, message: 'File deleted' });
    });
});

app.post('/api/list', authMiddleware, (req, res) => {
    const { category = '' } = req.body;
    const listPath = path.join(UPLOAD_DIR, category);
    
    if (!path.resolve(listPath).startsWith(path.resolve(UPLOAD_DIR))) {
        return res.status(403).json({ 
            success: false, 
            error: 'Invalid path' 
        });
    }
    
    fs.readdir(listPath, (err, files) => {
        if (err) {
            if (err.code === 'ENOENT') {
                return res.json({ success: true, files: [] });
            }
            return res.status(500).json({ 
                success: false, 
                error: `Failed to read directory: ${err.message}` 
            });
        }
        
        const fileInfos = files.map(file => {
            const filePath = path.join(listPath, file);
            const stats = fs.statSync(filePath);
            return {
                name: file,
                size: stats.size,
                createdAt: stats.birthtime,
                modifiedAt: stats.mtime,
                isDirectory: stats.isDirectory(),
                url: `${FILE_SERVER_BASE_URL}/${category ? category + '/' : ''}${file}`
            };
        });
        
        res.json({ success: true, files: fileInfos });
    });
});

app.use((err, req, res, next) => {
    if (err instanceof multer.MulterError) {
        if (err.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ 
                success: false, 
                error: 'File size exceeds limit (max 50MB)' 
            });
        }
        if (err.code === 'LIMIT_FILE_COUNT') {
            return res.status(400).json({ 
                success: false, 
                error: 'Too many files (max 20)' 
            });
        }
        return res.status(400).json({ 
            success: false, 
            error: `Upload error: ${err.message}` 
        });
    }
    
    if (err.message && err.message.includes('Blocked file type')) {
        return res.status(400).json({ 
            success: false, 
            error: err.message 
        });
    }
    
    console.error(`[Error] ${err.message}`);
    res.status(500).json({ 
        success: false, 
        error: 'Internal server error' 
    });
});

if (process.env.NODE_ENV !== 'test') {
    app.listen(PORT, '127.0.0.1', () => {
        console.log(`[Server] File upload API running on port ${PORT}`);
        console.log(`[Server] Upload directory: ${UPLOAD_DIR}`);
        console.log(`[Server] File server base URL: ${FILE_SERVER_BASE_URL}`);
    });
}

module.exports = { app, authMiddleware, getCategory };
