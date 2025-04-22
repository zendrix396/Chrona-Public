import axios from 'axios';

// API base URL - will use environment variable in production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://chrona-backend.onrender.com';

// Create an Axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Type definitions
export interface Task {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface TaskCreate {
  name: string;
  description?: string;
}

export interface TimeEntry {
  id: string;
  task_id: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  notes?: string;
  created_at: string;
  task?: Task;
}

export interface TimeEntryCreate {
  task_id: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  notes?: string;
}

export interface TimeEntryUpdate {
  end_time?: string;
  duration?: number;
  notes?: string;
}

export interface DailyStats {
  date: string;
  total_duration: number;
  tasks: {
    task_id: string;
    task_name: string;
    duration: number;
  }[];
}

export interface WeeklyStats {
  week_start: string;
  week_end: string;
  total_duration: number;
  daily_breakdown: {
    date: string;
    duration: number;
  }[];
  task_breakdown: {
    task_id: string;
    task_name: string;
    duration: number;
  }[];
}

// API endpoints
export const apiService = {
  // Tasks
  getTasks: async (): Promise<Task[]> => {
    const response = await api.get('/tasks/');
    return response.data;
  },
  
  createTask: async (task: TaskCreate): Promise<Task> => {
    const response = await api.post('/tasks/', task);
    return response.data;
  },
  
  deleteTask: async (id: string): Promise<void> => {
    await api.delete(`/tasks/${id}`);
  },
  
  // Time Entries
  getTimeEntries: async (): Promise<TimeEntry[]> => {
    const response = await api.get('/time-entries/');
    return response.data;
  },
  
  createTimeEntry: async (timeEntry: TimeEntryCreate): Promise<TimeEntry> => {
    const response = await api.post('/time-entries/', timeEntry);
    return response.data;
  },
  
  updateTimeEntry: async (id: string, timeEntry: TimeEntryUpdate): Promise<TimeEntry> => {
    const response = await api.put(`/time-entries/${id}`, timeEntry);
    return response.data;
  },
  
  deleteTimeEntry: async (id: string): Promise<void> => {
    await api.delete(`/time-entries/${id}`);
  },
  
  // Statistics
  getDailyStats: async (): Promise<DailyStats> => {
    const response = await api.get('/stats/daily');
    return response.data;
  },
  
  getWeeklyStats: async (): Promise<WeeklyStats> => {
    const response = await api.get('/stats/weekly');
    return response.data;
  },
};

export default apiService; 