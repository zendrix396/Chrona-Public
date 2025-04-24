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
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  TextField, 
  CircularProgress, 
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon, 
  Stop as StopIcon 
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService, { Task, TimeEntry, TimeEntryCreate, TimeEntryUpdate } from '../services/api';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';

// Extend dayjs with duration plugin
dayjs.extend(duration);

const TimeEntries: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<string | ''>('');
  const [notes, setNotes] = useState('');
  const queryClient = useQueryClient();
  
  // Queries
  const { data: tasks, isLoading: isLoadingTasks } = useQuery({
    queryKey: ['tasks'],
    queryFn: apiService.getTasks,
  });
  
  const { data: timeEntries, isLoading: isLoadingEntries } = useQuery({
    queryKey: ['timeEntries'],
    queryFn: apiService.getTimeEntries,
  });
  
  // Mutations
  const createMutation = useMutation({
    mutationFn: apiService.createTimeEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeEntries'] });
      handleClose();
    },
  });
  
  const updateMutation = useMutation({
    mutationFn: (params: { id: string; data: TimeEntryUpdate }) => 
      apiService.updateTimeEntry(params.id, params.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeEntries'] });
    },
  });
  
  const deleteMutation = useMutation({
    mutationFn: apiService.deleteTimeEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeEntries'] });
    },
  });
  
  const handleOpen = () => {
    setOpen(true);
  };
  
  const handleClose = () => {
    setOpen(false);
    setSelectedTask('');
    setNotes('');
  };
  
  const handleStartTimer = () => {
    if (selectedTask === '') return;
    
    const newEntry: TimeEntryCreate = {
      task_id: selectedTask,
      start_time: new Date().toISOString(),
      notes: notes || undefined,
    };
    
    createMutation.mutate(newEntry);
  };
  
  const handleStopTimer = (entry: TimeEntry) => {
    if (!entry.end_time) {
      updateMutation.mutate({
        id: entry.id,
        data: {
          end_time: new Date().toISOString(),
        },
      });
    }
  };
  
  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this time entry?')) {
      deleteMutation.mutate(id);
    }
  };
  
  const formatDateTime = (dateString: string) => {
    return dayjs(dateString).format('MMM D, YYYY h:mm A');
  };
  
  const formatDuration = (minutes: number | undefined) => {
    if (!minutes) return '---';
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };
  
  const getCurrentDuration = (entry: TimeEntry) => {
    if (entry.duration) return formatDuration(entry.duration);
    if (!entry.end_time) {
      const start = dayjs(entry.start_time);
      const now = dayjs();
      const diffMinutes = now.diff(start, 'minute');
      return formatDuration(diffMinutes);
    }
    return '---';
  };
  
  const isRunning = (entry: TimeEntry) => {
    return !!entry.start_time && !entry.end_time;
  };
  
  if (isLoadingTasks || isLoadingEntries) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Time Entries</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          onClick={handleOpen}
        >
          Start New Timer
        </Button>
      </Box>
      
      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow>
              <TableCell>Task</TableCell>
              <TableCell>Start Time</TableCell>
              <TableCell>End Time</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Notes</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {timeEntries && timeEntries.map((entry) => (
              <TableRow 
                key={entry.id}
                sx={{ 
                  '&:last-child td, &:last-child th': { border: 0 },
                  backgroundColor: isRunning(entry) ? 'rgba(63, 81, 181, 0.1)' : 'inherit',
                }}
              >
                <TableCell component="th" scope="row">
                  {entry.task?.name || `Task #${entry.task_id}`}
                </TableCell>
                <TableCell>{formatDateTime(entry.start_time)}</TableCell>
                <TableCell>
                  {entry.end_time ? formatDateTime(entry.end_time) : 'Running...'}
                </TableCell>
                <TableCell>{getCurrentDuration(entry)}</TableCell>
                <TableCell>{entry.notes || '-'}</TableCell>
                <TableCell align="right">
                  {isRunning(entry) && (
                    <Tooltip title="Stop Timer">
                      <IconButton 
                        color="primary" 
                        onClick={() => handleStopTimer(entry)}
                      >
                        <StopIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                  <Tooltip title="Delete">
                    <IconButton 
                      color="error" 
                      onClick={() => handleDelete(entry.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {(!timeEntries || timeEntries.length === 0) && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No time entries yet. Start tracking your time!
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* New Timer Dialog */}
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Start New Timer</DialogTitle>
        <DialogContent>
          <Box sx={{ my: 2, minWidth: 400 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel id="task-select-label">Task</InputLabel>
              <Select
                labelId="task-select-label"
                value={selectedTask}
                label="Task"
                onChange={(e) => setSelectedTask(e.target.value as string | '')}
              >
                {tasks && tasks.map((task) => (
                  <MenuItem key={task.id} value={task.id}>
                    {task.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Notes"
              fullWidth
              multiline
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button 
            onClick={handleStartTimer} 
            disabled={selectedTask === ''}
            variant="contained"
          >
            Start Timer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TimeEntries; 