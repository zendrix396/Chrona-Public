import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Box, Grid, Paper, Typography, CircularProgress, Card, CardContent, useTheme, useMediaQuery } from '@mui/material';
import apiService from '../services/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';
import dayjs from 'dayjs';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  // Use chart colors from theme
  const neonGreen = theme.palette.chart.green;
  const darkGreen = theme.palette.chart.darkGreen;
  
  // Fetch data using React Query
  const { data: dailyStats, isLoading: isDailyLoading } = useQuery({
    queryKey: ['dailyStats'],
    queryFn: apiService.getDailyStats,
  });

  const { data: weeklyStats, isLoading: isWeeklyLoading } = useQuery({
    queryKey: ['weeklyStats'],
    queryFn: apiService.getWeeklyStats,
  });

  // Format time duration
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  // Prepare chart data
  const dailyChartData = weeklyStats ? {
    labels: weeklyStats.daily_breakdown.map(day => dayjs(day.date).format('ddd, MMM D')),
    datasets: [
      {
        label: 'Time Spent (minutes)',
        data: weeklyStats.daily_breakdown.map(day => day.duration),
        backgroundColor: neonGreen,
        borderColor: darkGreen,
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  } : { labels: [], datasets: [] };

  const taskChartData = weeklyStats ? {
    labels: weeklyStats.task_breakdown.map(task => task.task_name),
    datasets: [
      {
        label: 'Time Spent (minutes)',
        data: weeklyStats.task_breakdown.map(task => task.duration),
        backgroundColor: [
          theme.palette.chart.green,
          theme.palette.chart.darkGreen,
          theme.palette.chart.lightGreen,
          'rgba(76, 175, 80, 0.7)',
          'rgba(139, 195, 74, 0.7)',
          'rgba(104, 210, 127, 0.7)',
        ],
        borderColor: 'rgba(0, 0, 0, 0.2)',
        borderWidth: 1,
      },
    ],
  } : { labels: [], datasets: [] };

  // Chart options with dark theme colors
  const chartOptions = {
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Minutes',
          color: 'rgba(255, 255, 255, 0.7)',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.7)',
        }
      },
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.7)',
          maxRotation: isMobile ? 45 : 0,
          minRotation: isMobile ? 45 : 0,
        }
      }
    },
    plugins: {
      legend: {
        labels: {
          color: 'rgba(255, 255, 255, 0.7)',
        }
      }
    }
  };

  const pieChartOptions = {
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: 'rgba(255, 255, 255, 0.7)',
          padding: 15,
          usePointStyle: true,
          pointStyle: 'circle',
        }
      }
    }
  };

  if (isDailyLoading || isWeeklyLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress sx={{ color: theme.palette.primary.main }} />
      </Box>
    );
  }

  const cardStyles = {
    bgcolor: 'rgba(17, 17, 17, 0.7)',
    borderRadius: 2,
    border: '1px solid rgba(0, 255, 65, 0.1)',
    backdropFilter: 'blur(10px)',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
    transition: 'transform 0.2s, box-shadow 0.2s',
    '&:hover': {
      transform: 'translateY(-3px)',
      boxShadow: `0 6px 20px rgba(0, 255, 65, 0.15)`,
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography 
        variant="h4" 
        gutterBottom 
        sx={{ 
          fontWeight: 700, 
          mb: 4, 
          fontSize: { xs: '1.75rem', sm: '2.5rem' },
          textShadow: '0 0 10px rgba(0, 255, 65, 0.3)',
          color: '#fff',
        }}
      >
        Time Tracking Dashboard
      </Typography>
      
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={cardStyles}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography color="rgba(255, 255, 255, 0.7)" sx={{ fontSize: '0.875rem' }} gutterBottom>
                Today's Total
              </Typography>
              <Typography 
                variant="h4" 
                sx={{ 
                  color: theme.palette.primary.main,
                  fontSize: { xs: '1.5rem', sm: '2rem' },
                  fontWeight: 700
                }}
              >
                {dailyStats ? formatDuration(dailyStats.total_duration) : '0h 0m'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={cardStyles}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography color="rgba(255, 255, 255, 0.7)" sx={{ fontSize: '0.875rem' }} gutterBottom>
                This Week's Total
              </Typography>
              <Typography 
                variant="h4" 
                sx={{ 
                  color: theme.palette.primary.main,
                  fontSize: { xs: '1.5rem', sm: '2rem' },
                  fontWeight: 700
                }}
              >
                {weeklyStats ? formatDuration(weeklyStats.total_duration) : '0h 0m'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={cardStyles}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography color="rgba(255, 255, 255, 0.7)" sx={{ fontSize: '0.875rem' }} gutterBottom>
                Most Time On
              </Typography>
              <Typography 
                variant="h5" 
                sx={{ 
                  color: '#fff',
                  fontSize: { xs: '1.25rem', sm: '1.5rem' },
                  fontWeight: 600,
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap'
                }}
              >
                {weeklyStats && weeklyStats.task_breakdown.length > 0
                  ? weeklyStats.task_breakdown.sort((a, b) => b.duration - a.duration)[0].task_name
                  : 'No tasks yet'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Daily Breakdown Bar Chart */}
        <Grid item xs={12} lg={8}>
          <Paper 
            sx={{ 
              p: { xs: 2, sm: 3 }, 
              bgcolor: 'rgba(17, 17, 17, 0.7)', 
              borderRadius: 2,
              border: '1px solid rgba(0, 255, 65, 0.1)',
              backdropFilter: 'blur(10px)',
              height: '100%',
            }}
          >
            <Typography 
              variant="h6" 
              gutterBottom
              sx={{ 
                fontWeight: 600, 
                color: '#fff',
                fontSize: { xs: '1rem', sm: '1.25rem' }
              }}
            >
              Daily Breakdown
            </Typography>
            <Box sx={{ height: { xs: 250, sm: 300, md: 350 }, mt: 2 }}>
              <Bar 
                data={dailyChartData} 
                options={chartOptions} 
              />
            </Box>
          </Paper>
        </Grid>
        
        {/* Task Distribution Pie Chart */}
        <Grid item xs={12} sm={6} lg={4}>
          <Paper 
            sx={{ 
              p: { xs: 2, sm: 3 }, 
              bgcolor: 'rgba(17, 17, 17, 0.7)', 
              borderRadius: 2,
              border: '1px solid rgba(0, 255, 65, 0.1)',
              backdropFilter: 'blur(10px)',
              height: '100%',
            }}
          >
            <Typography 
              variant="h6" 
              gutterBottom
              sx={{ 
                fontWeight: 600, 
                color: '#fff',
                fontSize: { xs: '1rem', sm: '1.25rem' }
              }}
            >
              Task Distribution
            </Typography>
            <Box 
              sx={{ 
                height: { xs: 220, sm: 240, md: 280 }, 
                display: 'flex', 
                justifyContent: 'center',
                mt: 2
              }}
            >
              <Pie 
                data={taskChartData} 
                options={pieChartOptions} 
              />
            </Box>
          </Paper>
        </Grid>

        {/* Today's Tasks */}
        <Grid item xs={12}>
          <Paper 
            sx={{ 
              p: { xs: 2, sm: 3 }, 
              bgcolor: 'rgba(17, 17, 17, 0.7)', 
              borderRadius: 2,
              border: '1px solid rgba(0, 255, 65, 0.1)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <Typography 
              variant="h6" 
              gutterBottom
              sx={{ 
                fontWeight: 600, 
                color: '#fff',
                fontSize: { xs: '1rem', sm: '1.25rem' },
                mb: 3
              }}
            >
              Today's Tasks
            </Typography>
            {dailyStats && dailyStats.tasks.length > 0 ? (
              <Grid container spacing={2}>
                {dailyStats.tasks.map((task) => (
                  <Grid item xs={12} sm={6} md={4} key={task.task_id}>
                    <Card 
                      sx={{
                        bgcolor: 'rgba(0, 0, 0, 0.4)',
                        borderRadius: 2,
                        border: '1px solid rgba(0, 255, 65, 0.05)',
                        transition: 'all 0.2s',
                        '&:hover': {
                          borderColor: 'rgba(0, 255, 65, 0.2)',
                          boxShadow: '0 0 15px rgba(0, 255, 65, 0.1)'
                        }
                      }}
                    >
                      <CardContent>
                        <Typography 
                          sx={{ 
                            fontSize: { xs: '1rem', sm: '1.125rem' },
                            fontWeight: 600,
                            color: '#fff',
                            mb: 1
                          }}
                        >
                          {task.task_name}
                        </Typography>
                        <Typography 
                          sx={{ 
                            color: theme.palette.primary.main,
                            fontWeight: 500
                          }}
                        >
                          {formatDuration(task.duration)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Typography sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>No tracked tasks today</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 