import React, { ReactNode, useState, useEffect } from 'react';
import { 
  AppBar, 
  Box, 
  CssBaseline, 
  Divider, 
  Drawer, 
  IconButton, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText, 
  Toolbar, 
  Typography,
  Avatar,
  Container,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { 
  Menu as MenuIcon, 
  Dashboard as DashboardIcon, 
  AccessTime as TimeIcon, 
  List as ListIcon,
  Timer as TimerIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

const drawerWidth = 260;

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Close drawer when clicking a link on mobile
  useEffect(() => {
    if (isMobile && mobileOpen) {
      setMobileOpen(false);
    }
  }, [location.pathname, isMobile]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const navItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Time Entries', icon: <TimeIcon />, path: '/time-entries' },
    { text: 'Tasks', icon: <ListIcon />, path: '/tasks' },
  ];

  const drawerContent = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(180deg, #111111 0%, #080808 100%)',
      }}
    >
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 1
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            sx={{
              bgcolor: theme.palette.primary.main,
              color: '#000',
              width: 40,
              height: 40,
              boxShadow: '0 0 10px rgba(0, 255, 65, 0.5)',
            }}
          >
            <TimerIcon />
          </Avatar>
          <Typography variant="h6" color="white" fontWeight="bold">
            Time Tracker
          </Typography>
        </Box>
        {isMobile && (
          <IconButton 
            onClick={handleDrawerToggle} 
            sx={{ color: 'rgba(255,255,255,0.7)' }}
          >
            <CloseIcon />
          </IconButton>
        )}
      </Box>
      <Divider sx={{ bgcolor: 'rgba(0, 255, 65, 0.1)' }} />
      <List sx={{ flexGrow: 1, px: 1, py: 2 }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
              <ListItemButton 
                component={Link} 
                to={item.path}
                selected={isActive}
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  '&.Mui-selected': {
                    bgcolor: 'rgba(0, 255, 65, 0.15)',
                    '&:hover': {
                      bgcolor: 'rgba(0, 255, 65, 0.25)',
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      left: 0,
                      top: '20%',
                      height: '60%',
                      width: 4,
                      bgcolor: theme.palette.primary.main,
                      borderRadius: '0 4px 4px 0',
                      boxShadow: '0 0 8px rgba(0, 255, 65, 0.8)',
                    }
                  },
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                  }
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive ? theme.palette.primary.main : 'rgba(255, 255, 255, 0.6)',
                    minWidth: 40
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  sx={{
                    '& .MuiTypography-root': {
                      fontWeight: isActive ? 600 : 400,
                      color: isActive ? theme.palette.primary.main : 'rgba(255, 255, 255, 0.8)',
                      fontSize: { xs: '0.95rem', sm: '1rem' }
                    }
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      <Box
        sx={{
          p: 2,
          borderTop: '1px solid rgba(0, 255, 65, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography variant="caption" color="rgba(255,255,255,0.5)" fontSize={11}>
          © {new Date().getFullYear()} Time Tracker
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: theme.palette.background.default }}>
      <CssBaseline />
      
      {/* Floating AppBar */}
      <AppBar
        position="fixed"
        color="transparent"
        elevation={0}
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          bgcolor: 'transparent',
          boxShadow: 'none',
          pt: { xs: 1, sm: 2 },
          px: { xs: 1, sm: 2 },
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Box
          sx={{
            bgcolor: 'rgba(17, 17, 17, 0.8)',
            backdropFilter: 'blur(10px)',
            borderRadius: 3,
            boxShadow: '0 4px 30px rgba(0, 255, 65, 0.1)',
            border: '1px solid rgba(0, 255, 65, 0.1)',
          }}
        >
          <Toolbar sx={{ justifyContent: 'space-between', minHeight: { xs: '56px', sm: '64px' } }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ mr: 1, display: { sm: 'none' } }}
              >
                <MenuIcon />
              </IconButton>
              <Typography 
                variant="h6" 
                noWrap 
                component="div" 
                fontWeight="bold"
                sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
              >
                {navItems.find(item => item.path === location.pathname)?.text || 'Time Tracker'}
              </Typography>
            </Box>
            
            {/* Navigation icons for desktop view */}
            <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1 }}>
              {navItems.map((item) => (
                <IconButton
                  key={item.text}
                  component={Link}
                  to={item.path}
                  color={location.pathname === item.path ? 'primary' : 'inherit'}
                  size="small"
                  sx={{
                    borderRadius: 2,
                    p: 1,
                    bgcolor: location.pathname === item.path ? 'rgba(0, 255, 65, 0.1)' : 'transparent',
                    '&:hover': {
                      bgcolor: 'rgba(0, 255, 65, 0.05)',
                    }
                  }}
                >
                  {item.icon}
                </IconButton>
              ))}
            </Box>
          </Toolbar>
        </Box>
      </AppBar>
      
      {/* Drawer for navigation */}
      <Box
        component="nav"
        sx={{ 
          width: { sm: drawerWidth }, 
          flexShrink: { sm: 0 },
        }}
        aria-label="navigation"
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: '85%', // Use percentage for better mobile experience
              maxWidth: 300,
              bgcolor: '#111111',
              borderRight: '1px solid rgba(0, 255, 65, 0.1)',
            },
            '& .MuiBackdrop-root': {
              backgroundColor: 'rgba(0, 0, 0, 0.7)',
            }
          }}
        >
          {drawerContent}
        </Drawer>
        
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              bgcolor: '#111111',
              borderRight: '1px solid rgba(0, 255, 65, 0.05)',
              boxShadow: '4px 0 15px rgba(0, 0, 0, 0.3)',
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>
      
      {/* Main content */}
      <Box
        component="main"
        sx={{ 
          flexGrow: 1, 
          px: { xs: 1.5, sm: 3 }, 
          py: { xs: 2, sm: 3 },
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: { xs: 7, sm: 9 }, 
          display: 'flex',
          flexDirection: 'column',
          overflowX: 'hidden',
        }}
      >
        <Container 
          maxWidth="lg" 
          sx={{ 
            flexGrow: 1, 
            px: { xs: 1, sm: 2 },
            py: 1,
          }}
        >
          {children}
        </Container>
      </Box>
    </Box>
  );
};

export default Layout; 