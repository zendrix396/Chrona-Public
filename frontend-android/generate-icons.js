const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const ASSETS_DIR = path.join(__dirname, 'assets');

// Create assets directory if it doesn't exist
if (!fs.existsSync(ASSETS_DIR)) {
  fs.mkdirSync(ASSETS_DIR, { recursive: true });
  console.log('Created assets directory');
}

// Generate a simple colored icon with text
async function generateIcon(filename, size, text, backgroundColor = '#4630EB') {
  const svgText = `
    <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="${backgroundColor}"/>
      <text 
        x="50%" 
        y="50%" 
        font-family="Arial, sans-serif" 
        font-size="${size / 6}px" 
        fill="white" 
        text-anchor="middle" 
        dominant-baseline="middle"
      >
        ${text}
      </text>
    </svg>
  `;

  const outputPath = path.join(ASSETS_DIR, filename);
  
  await sharp(Buffer.from(svgText))
    .png()
    .toFile(outputPath);
    
  console.log(`Created ${filename}`);
}

// Generate all required icon files
async function generateAllIcons() {
  try {
    // App icon (used on home screen)
    await generateIcon('icon.png', 1024, 'Chrona', '#3498db');
    
    // Adaptive icon foreground (Android)
    await generateIcon('adaptive-icon.png', 1024, 'Chrona', '#3498db');
    
    // Splash screen
    await generateIcon('splash.png', 1242, 'Chrona', '#3498db');
    
    // Favicon for web
    await generateIcon('favicon.png', 196, 'C', '#3498db');
    
    console.log('All icon files generated successfully!');
  } catch (error) {
    console.error('Error generating icons:', error);
  }
}

// Run the icon generation
generateAllIcons(); 