import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import AchatDashboard from "./pages/achat/AchatDashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";
import LaboDashboard from "./pages/labo/LaboDashboard";
import LoginPage from "./pages/LoginPage";
import StudentDashboard from "./pages/student/StudentDashboard";
import TeacherDashboard from "./pages/teacher/TeacherDashboard";

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="container py-5">Chargement...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  const target = {
    etudiant: "/student",
    encadrant: "/teacher",
    labo: "/labo",
    achat: "/achat",
    admin: "/admin"
  }[user.role];
  return <Navigate to={target || "/login"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<HomeRedirect />} />

      <Route
        path="/student"
        element={
          <ProtectedRoute allowedRoles={["etudiant"]}>
            <StudentDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/teacher"
        element={
          <ProtectedRoute allowedRoles={["encadrant"]}>
            <TeacherDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/labo"
        element={
          <ProtectedRoute allowedRoles={["labo"]}>
            <LaboDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/achat"
        element={
          <ProtectedRoute allowedRoles={["achat"]}>
            <AchatDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={["admin"]}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
