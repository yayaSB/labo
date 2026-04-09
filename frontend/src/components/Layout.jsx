import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import NotificationsPanel from "../pages/common/NotificationsPanel";

const navByRole = {
  etudiant: [{ to: "/student", label: "Dashboard Etudiant" }],
  encadrant: [{ to: "/teacher", label: "Dashboard Encadrant" }],
  labo: [{ to: "/labo", label: "Dashboard Labo" }],
  achat: [{ to: "/achat", label: "Dashboard Achat" }],
  admin: [{ to: "/admin", label: "Dashboard Admin" }]
};

export default function Layout({ title, children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const links = navByRole[user?.role] || [];

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="container-fluid py-3">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h2 className="mb-0">{title}</h2>
          <small className="text-muted">
            {user?.first_name} {user?.last_name} ({user?.role})
          </small>
        </div>
        <button className="btn btn-danger" onClick={handleLogout}>
          Se deconnecter
        </button>
      </div>

      <div className="mb-3 d-flex gap-2">
        {links.map((item) => (
          <Link key={item.to} to={item.to} className="btn btn-outline-primary btn-sm">
            {item.label}
          </Link>
        ))}
      </div>

      <div className="row g-3">
        <div className="col-lg-9">{children}</div>
        <div className="col-lg-3">
          <NotificationsPanel />
        </div>
      </div>
    </div>
  );
}
