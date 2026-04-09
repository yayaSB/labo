import { useEffect, useState } from "react";
import api from "../../api/client";

export default function NotificationsPanel() {
  const [notifications, setNotifications] = useState([]);

  const loadNotifications = async () => {
    try {
      const response = await api.get("/notifications");
      setNotifications(response.data);
    } catch (error) {
      // Silent fail in UI panel.
    }
  };

  const markRead = async (id) => {
    await api.put(`/notifications/${id}/read`);
    setNotifications((prev) =>
      prev.map((item) => (item.id === id ? { ...item, is_read: true } : item))
    );
  };

  useEffect(() => {
    loadNotifications();
    const timer = setInterval(loadNotifications, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="card mt-3">
      <div className="card-header">Notifications</div>
      <div className="list-group list-group-flush notification-scroll">
        {notifications.length === 0 && (
          <div className="list-group-item text-muted">Aucune notification</div>
        )}
        {notifications.map((n) => (
          <div key={n.id} className="list-group-item">
            <div className="d-flex justify-content-between gap-2">
              <small className={n.is_read ? "text-muted" : "fw-semibold"}>{n.message}</small>
              {!n.is_read && (
                <button
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => markRead(n.id)}
                >
                  Lu
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
