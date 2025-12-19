import { put } from '@vercel/blob';
import { IncomingForm } from 'formidable';
import fs from 'fs';

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const form = new IncomingForm();

    const { fields, files } = await new Promise((resolve, reject) => {
      form.parse(req, (err, fields, files) => {
        if (err) reject(err);
        else resolve({ fields, files });
      });
    });

    const file = files.file?.[0] || files.file;
    const type = fields.type?.[0] || fields.type || 'file';

    if (!file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    // Read file buffer
    const fileBuffer = fs.readFileSync(file.filepath);

    // Generate unique filename
    const timestamp = Date.now();
    const extension = type === 'audio' ? 'webm' : (file.originalFilename?.split('.').pop() || 'jpg');
    const filename = `intake/${type}/${timestamp}-${Math.random().toString(36).substring(7)}.${extension}`;

    // Upload to Vercel Blob
    const blob = await put(filename, fileBuffer, {
      access: 'public',
      contentType: file.mimetype,
    });

    // Clean up temp file
    fs.unlinkSync(file.filepath);

    return res.status(200).json({ url: blob.url });
  } catch (error) {
    console.error('Upload error:', error);
    return res.status(500).json({ error: 'Upload failed' });
  }
}
