import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Layout from './components/Layout';
import TimeEntries from './pages/TimeEntries';
import Tasks from './pages/Tasks';

const App: React.FC = () => {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/time-entries" element={<TimeEntries />} />
        <Route path="/tasks" element={<Tasks />} />
      </Routes>
    </Layout>
  );
};

export default App; 