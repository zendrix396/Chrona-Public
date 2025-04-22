import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';

// Create a client for React Query
const queryClient = new QueryClient();

// Create MUI theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00FF41', // Neon green
    },
    secondary: {
      main: '#39FF14', // Even brighter neon green
    },
    background: {
      default: '#080808', // Almost pure black
      paper: '#111111',   // Very dark gray
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#B0B0B0',
    },
    // Define custom colors for charts
    chart: {
      green: '#00FF41',
      darkGreen: '#00BB41',
      lightGreen: '#66FF66',
    },
  },
  shape: {
    borderRadius: 12, // Rounded corners for all components
  },
  typography: {
    fontFamily: "'Inter', 'Roboto', 'Helvetica', 'Arial', sans-serif",
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 700 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none', // Remove default gradient
          boxShadow: '0 4px 15px rgba(0, 255, 65, 0.15)',
          border: '1px solid rgba(0, 255, 65, 0.07)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 20px 0 rgba(0, 255, 65, 0.14), 0 7px 10px -5px rgba(0, 255, 65, 0.2)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
        },
        containedPrimary: {
          boxShadow: '0 4px 8px 0 rgba(0, 255, 65, 0.25)',
          '&:hover': {
            boxShadow: '0 8px 16px 0 rgba(0, 255, 65, 0.3)',
          },
        },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '6px',
            height: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#080808',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0, 255, 65, 0.3)',
            borderRadius: '3px',
            '&:hover': {
              backgroundColor: 'rgba(0, 255, 65, 0.5)',
            },
          },
        },
      },
    },
  },
});

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>
); 