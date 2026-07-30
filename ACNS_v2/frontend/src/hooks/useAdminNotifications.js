import { useState, useEffect, useCallback, useMemo } from 'react';
import { getIssues } from '../services/api';

const ADMIN_NOTIF_STORAGE_KEY = 'admin_notifications_state';

const getTimeAgo = (dateString) => {
  if (!dateString) return 'Unknown time';
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();
};

export const useAdminNotifications = (refreshInterval = 15000) => {
  const [issues, setIssues] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const storageKey = ADMIN_NOTIF_STORAGE_KEY;

  useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const data = JSON.parse(stored);
        setNotifications(data.notifications || []);
      }
    } catch (e) {
      console.error('Failed to load admin notifications from storage:', e);
    }
  }, [storageKey]);

  const saveToStorage = useCallback((notifs) => {
    try {
      localStorage.setItem(storageKey, JSON.stringify({
        notifications: notifs,
        lastUpdated: new Date().toISOString(),
      }));
    } catch (e) {
      console.error('Failed to save admin notifications:', e);
    }
  }, [storageKey]);

  const fetchAndDeriveNotifications = useCallback(async () => {
    try {
      const res = await getIssues({ role: 'admin' });
      const newIssues = Array.isArray(res.data) ? res.data : [];
      
      setIssues(newIssues);
      
      const derivedNotifications = [];
      const seenIds = new Set();
      const fetchTime = new Date().toISOString();

      newIssues.forEach(issue => {
        const timestamp = issue.createdAt || issue.updatedAt;

        if (!seenIds.has(`new-${issue.id}`)) {
          seenIds.add(`new-${issue.id}`);
          derivedNotifications.push({
            id: `new-${issue.id}`,
            type: 'new',
            title: 'New issue reported',
            description: `${issue.category || 'Issue'} at ${issue.location?.text || 'Unknown location'}`,
            timestamp: fetchTime,
            issueId: issue.id,
          });
        }

        if (issue.status === 'Resolved' || issue.status === 'Closed') {
          if (!seenIds.has(`resolved-${issue.id}`)) {
            seenIds.add(`resolved-${issue.id}`);
            derivedNotifications.push({
              id: `resolved-${issue.id}`,
              type: 'resolved',
              title: 'Issue resolved',
              description: `${issue.category || 'Issue'} has been resolved`,
              timestamp: fetchTime,
              issueId: issue.id,
            });
          }
        }

        if (issue.status === 'In Progress') {
          if (!seenIds.has(`progress-${issue.id}`)) {
            seenIds.add(`progress-${issue.id}`);
            derivedNotifications.push({
              id: `progress-${issue.id}`,
              type: 'in_progress',
              title: 'Issue in progress',
              description: `${issue.category || 'Issue'} is being worked on`,
              timestamp: fetchTime,
              issueId: issue.id,
            });
          }
        }
      });

      derivedNotifications.sort((a, b) => {
        const dateA = new Date(a.timestamp || 0);
        const dateB = new Date(b.timestamp || 0);
        return dateB - dateA;
      });

      setNotifications(derivedNotifications.slice(0, 50));
      saveToStorage(derivedNotifications.slice(0, 50));
    } catch (err) {
      console.error('Failed to fetch admin notifications:', err);
    } finally {
      setLoading(false);
    }
  }, [saveToStorage]);

  useEffect(() => {
    fetchAndDeriveNotifications();
    const interval = setInterval(fetchAndDeriveNotifications, refreshInterval);
    const handleFocus = () => fetchAndDeriveNotifications();
    window.addEventListener('focus', handleFocus);
    return () => {
      clearInterval(interval);
      window.removeEventListener('focus', handleFocus);
    };
  }, [fetchAndDeriveNotifications, refreshInterval]);

  const getReadState = useCallback(() => {
    try {
      const stored = localStorage.getItem(`${storageKey}_read`) || '[]';
      return new Set(JSON.parse(stored));
    } catch {
      return new Set();
    }
  }, [storageKey]);

  const markAsRead = useCallback((notificationId) => {
    const readSet = getReadState();
    readSet.add(notificationId);
    localStorage.setItem(`${storageKey}_read`, JSON.stringify([...readSet]));
  }, [storageKey, getReadState]);

  const markAllAsRead = useCallback(() => {
    const readIds = notifications.map(n => n.id);
    localStorage.setItem(`${storageKey}_read`, JSON.stringify(readIds));
  }, [storageKey, notifications]);

  const getUnreadCount = useMemo(() => {
    const readSet = getReadState();
    return notifications.filter(n => !readSet.has(n.id)).length;
  }, [notifications, getReadState]);

  const getRelativeTime = useCallback((timestamp) => {
    return getTimeAgo(timestamp);
  }, []);

  const getNotificationsWithReadState = useMemo(() => {
    const readSet = getReadState();
    return notifications.map(n => ({
      ...n,
      read: readSet.has(n.id)
    }));
  }, [notifications, getReadState]);

  return {
    notifications: getNotificationsWithReadState,
    unreadCount: getUnreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    getRelativeTime,
    refresh: fetchAndDeriveNotifications,
  };
};

export default useAdminNotifications;
