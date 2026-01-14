import { IncomingForm } from 'formidable';

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

    const { fields } = await new Promise((resolve, reject) => {
      form.parse(req, (err, fields, files) => {
        if (err) reject(err);
        else resolve({ fields, files });
      });
    });

    // Flatten fields (formidable returns arrays)
    const data = {};
    for (const [key, value] of Object.entries(fields)) {
      data[key] = Array.isArray(value) ? value[0] : value;
    }

    // Format the email body
    const emailBody = formatEmailBody(data);

    // Send via Resend
    const resendResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'Intake Form <intake@sailorskills.com>',
        to: ['standardhuman@gmail.com'],
        subject: `New Project Inquiry: ${data.company || 'Unknown Company'}`,
        html: emailBody,
        reply_to: data.email,
      }),
    });

    if (!resendResponse.ok) {
      const error = await resendResponse.text();
      console.error('Resend error:', error);
      throw new Error('Failed to send email');
    }

    // Redirect to thank you page
    res.writeHead(302, { Location: '/thank-you.html' });
    return res.end();
  } catch (error) {
    console.error('Form submission error:', error);
    return res.status(500).json({ error: 'Failed to submit form' });
  }
}

function formatEmailBody(data) {
  const sections = [
    {
      title: 'Contact Information',
      fields: [
        ['Name', data.name],
        ['Email', data.email],
        ['Phone', data.phone],
        ['Company', data.company],
      ],
    },
    {
      title: 'About Their Business',
      fields: [
        ['Business Description', data['business-description']],
        ['Current Website', data['current-website']],
        ['What\'s Working', data['site-working']],
        ['What\'s NOT Working', data['site-frustrations']],
        ['Ideal Customer', data['ideal-customer']],
        ['Market Positioning', data.positioning],
      ],
    },
    {
      title: 'Project Details',
      fields: [
        ['How Customers Find Them', data['lead-source']],
        ['Primary Conversion Goal', data['conversion-goal']],
        ['Project Type', data['project-type']],
        ['Pages Needed', data['pages-needed']],
        ['Features', data.features],
      ],
    },
    {
      title: 'Assets & Content',
      fields: [
        ['Has Logo', data['has-logo']],
        ['Has Photos', data['has-photos']],
        ['Has Copy', data['has-copy']],
      ],
    },
    {
      title: 'Design & Timeline',
      fields: [
        ['Inspiration Sites', data.inspiration],
        ['Why They Like Them', data['inspiration-why']],
        ['Timeline', data.timeline],
        ['Budget', data.budget],
      ],
    },
    {
      title: 'After Launch',
      fields: [
        ['Post-Launch Preference', data['post-launch']],
      ],
    },
    {
      title: 'Additional Info',
      fields: [
        ['Additional Details', data.additional],
        ['Referral Source', data.referral],
      ],
    },
  ];

  let html = `
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
      <h1 style="color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px;">New Project Inquiry</h1>
  `;

  for (const section of sections) {
    html += `<h2 style="color: #374151; font-size: 16px; margin-top: 24px; margin-bottom: 12px;">${section.title}</h2>`;
    html += '<table style="width: 100%; border-collapse: collapse;">';

    for (const [label, value] of section.fields) {
      if (value) {
        html += `
          <tr>
            <td style="padding: 8px 0; color: #6b7280; width: 140px; vertical-align: top;">${label}</td>
            <td style="padding: 8px 0; color: #111827;">${escapeHtml(value)}</td>
          </tr>
        `;
      }
    }

    html += '</table>';
  }

  // Add audio recording section if present
  if (data['audio-url']) {
    html += `
      <h2 style="color: #374151; font-size: 16px; margin-top: 24px; margin-bottom: 12px;">Voice Recording</h2>
      <p style="color: #111827;">
        <a href="${escapeHtml(data['audio-url'])}" style="color: #2563eb; text-decoration: underline;">Listen to recording</a>
      </p>
    `;
  }

  // Add images section if present
  if (data['image-urls']) {
    const imageUrls = data['image-urls'].split(',');
    html += `
      <h2 style="color: #374151; font-size: 16px; margin-top: 24px; margin-bottom: 12px;">Uploaded Images (${imageUrls.length})</h2>
      <div style="display: flex; flex-wrap: wrap; gap: 8px;">
    `;
    for (const url of imageUrls) {
      html += `
        <a href="${escapeHtml(url)}" target="_blank" style="display: inline-block;">
          <img src="${escapeHtml(url)}" style="width: 120px; height: 80px; object-fit: cover; border-radius: 4px; border: 1px solid #e5e7eb;">
        </a>
      `;
    }
    html += '</div>';
  }

  html += `
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin-top: 32px;">
      <p style="color: #9ca3af; font-size: 12px;">Submitted via intake.sailorskills.com</p>
    </div>
  `;

  return html;
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>');
}
