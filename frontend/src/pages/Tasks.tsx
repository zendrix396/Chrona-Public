import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper,
  Button, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField, 
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  Tooltip,
  Snackbar,
  Alert
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService, { TaskCreate } from '../services/api';
import dayjs from 'dayjs';

const Tasks: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [taskToDelete, setTaskToDelete] = useState<string | null>(null);
  const [taskName, setTaskName] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error'
  });
  const queryClient = useQueryClient();
  
  // Fetch tasks
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: apiService.getTasks,
  });
  
  // Create task mutation
  const createMutation = useMutation({
    mutationFn: apiService.createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      handleClose();
      setSnackbar({
        open: true,
        message: 'Task created successfully!',
        severity: 'success'
      });
    },
    onError: () => {
      setSnackbar({
        open: true,
        message: 'Failed to create task. Please try again.',
        severity: 'error'
      });
    }
  });
  
  // Delete task mutation
  const deleteMutation = useMutation({
    mutationFn: apiService.deleteTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setSnackbar({
        open: true,
        message: 'Task deleted successfully!',
        severity: 'success'
      });
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to delete task. It may have associated time entries.',
        severity: 'error'
      });
    }
  });
  
  const handleOpen = () => {
    setOpen(true);
  };
  
  const handleClose = () => {
    setOpen(false);
    setTaskName('');
    setTaskDescription('');
  };
  
  const handleCreateTask = () => {
    if (!taskName.trim()) return;
    
    const newTask: TaskCreate = {
      name: taskName.trim(),
      description: taskDescription.trim() || undefined,
    };
    
    createMutation.mutate(newTask);
  };
  
  const handleDeleteClick = (taskId: string) => {
    setTaskToDelete(taskId);
    setDeleteConfirmOpen(true);
  };
  
  const confirmDelete = () => {
    if (taskToDelete !== null) {
      deleteMutation.mutate(taskToDelete);
      setDeleteConfirmOpen(false);
      setTaskToDelete(null);
    }
  };
  
  const cancelDelete = () => {
    setDeleteConfirmOpen(false);
    setTaskToDelete(null);
  };
  
  const formatDate = (dateString: string) => {
    return dayjs(dateString).format('MMM D, YYYY');
  };
  
  const handleSnackbarClose = () => {
    setSnackbar({...snackbar, open: false});
  };
  
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Tasks</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          onClick={handleOpen}
        >
          Add New Task
        </Button>
      </Box>
      
      <Paper sx={{ p: 2 }}>
        {tasks && tasks.length > 0 ? (
          <List>
            {tasks.map((task, index) => (
              <React.Fragment key={task.id}>
                <ListItem alignItems="flex-start">
                  <ListItemText
                    primary={task.name}
                    secondary={
                      <>
                        <Typography
                          component="span"
                          variant="body2"
                          color="text.primary"
                        >
                          {task.description}
                        </Typography>
                        {task.description && <br />}
                        Created on {formatDate(task.created_at)}
                      </>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Tooltip title="Delete Task">
                      <IconButton edge="end" onClick={() => handleDeleteClick(task.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < tasks.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Typography sx={{ p: 2 }}>
            No tasks created yet. Add your first task to start tracking time!
          </Typography>
        )}
      </Paper>
      
      {/* New Task Dialog */}
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Add New Task</DialogTitle>
        <DialogContent>
          <Box sx={{ my: 2, minWidth: 400 }}>
            <TextField
              label="Task Name"
              fullWidth
              required
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={taskDescription}
              onChange={(e) => setTaskDescription(e.target.value)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button 
            onClick={handleCreateTask} 
            disabled={!taskName.trim()}
            variant="contained"
          >
            Create Task
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={cancelDelete}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this task? This action cannot be undone.
            
            Note: Tasks with time entries cannot be deleted.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelDelete}>Cancel</Button>
          <Button 
            onClick={confirmDelete} 
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleSnackbarClose} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Tasks; 