// Simple script to generate placeholder logos
const fs = require('fs');
const path = require('path');

// Create a simple SVG logo
const createSvgLogo = (size) => {
  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" fill="#2563eb" rx="${size * 0.1}"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="${size * 0.4}" font-weight="bold">P</text>
</svg>`;
};

// Generate logo files
const logos = [
  { name: 'logo192.png', size: 192 },
  { name: 'logo512.png', size: 512 }
];

console.log('Generating placeholder logos...');

// For now, let's just create empty files to prevent errors
logos.forEach(({ name }) => {
  const filePath = path.join(__dirname, '../../public', name);
  // Create empty file
  fs.writeFileSync(filePath, '');
  console.log(`Created placeholder: ${name}`);
});

console.log('Placeholder logos created!');