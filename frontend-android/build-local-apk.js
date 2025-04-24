/**
 * Build Local APK Script
 * 
 * This script provides step-by-step commands for building an APK locally
 * without needing an Expo account.
 * 
 * Usage:
 * 1. Run 'node build-local-apk.js'
 * 2. Follow the printed instructions
 */

const chalk = require('chalk') || { green: (text) => text, yellow: (text) => text, blue: (text) => text };

console.log(chalk.green('\n========== HOW TO BUILD CHRONA APK LOCALLY ==========\n'));

console.log(chalk.blue('Step 1:') + ' Generate native Android project files');
console.log('  npx expo prebuild --platform android --clean\n');

console.log(chalk.blue('Step 2:') + ' Navigate to Android directory');
console.log('  cd android\n');

console.log(chalk.blue('Step 3:') + ' Build the debug APK');
console.log('  .\\gradlew.bat assembleDebug\n');

console.log(chalk.blue('Step 4:') + ' Your APK will be located at:');
console.log(chalk.yellow('  android/app/build/outputs/apk/debug/app-debug.apk\n'));

console.log(chalk.blue('Alternative:') + ' Use Expo EAS (requires account)');
console.log('  npx eas build -p android --profile preview\n');

console.log(chalk.green('=====================================================\n'));

console.log('To execute these commands one-by-one, copy each command and run it in your terminal.\n'); 