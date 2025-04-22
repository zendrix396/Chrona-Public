import '@mui/material/styles';

declare module '@mui/material/styles' {
  interface PaletteOptions {
    chart?: {
      green: string;
      darkGreen: string;
      lightGreen: string;
    };
  }
  
  interface Palette {
    chart: {
      green: string;
      darkGreen: string;
      lightGreen: string;
    };
  }
} 