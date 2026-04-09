import { useEffect, useMemo, useState } from "react";
import { Bar, Pie } from "react-chartjs-2";
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip
} from "chart.js";
import api from "../../api/client";
import Layout from "../../components/Layout";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

export default function AdminDashboard() {
  const [encadrants, setEncadrants] = useState([]);
  const [etudiants, setEtudiants] = useState([]);
  const [stats, setStats] = useState(null);
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    departement: ""
  });
  const [studentForm, setStudentForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    classe: "",
    encadrant: ""
  });

  const loadData = async () => {
    const [eRes, etRes, sRes] = await Promise.all([
      api.get("/encadrants"),
      api.get("/etudiants"),
      api.get("/statistiques")
    ]);
    setEncadrants(eRes.data);
    setEtudiants(etRes.data);
    setStats(sRes.data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const createEncadrant = async (event) => {
    event.preventDefault();
    await api.post("/encadrants", form);
    setForm({
      username: "",
      email: "",
      password: "",
      first_name: "",
      last_name: "",
      departement: ""
    });
    loadData();
  };

  const deleteEncadrant = async (id) => {
    await api.delete(`/encadrants/${id}`);
    loadData();
  };

  const createStudent = async (event) => {
    event.preventDefault();
    await api.post("/etudiants", {
      ...studentForm,
      encadrant: studentForm.encadrant ? Number(studentForm.encadrant) : null
    });
    setStudentForm({
      username: "",
      email: "",
      password: "",
      first_name: "",
      last_name: "",
      classe: "",
      encadrant: ""
    });
    loadData();
  };

  const deleteStudent = async (id) => {
    await api.delete(`/etudiants/${id}`);
    loadData();
  };

  const downloadReport = async (format) => {
    const response = await api.get(`/rapports?format=${format}`, { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", format === "pdf" ? "labresa_rapport.pdf" : "labresa_rapport.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const chartStatusData = useMemo(() => {
    if (!stats) return null;
    return {
      labels: stats.demandes_par_statut.map((item) => item.statut),
      datasets: [
        {
          label: "Demandes",
          data: stats.demandes_par_statut.map((item) => item.total),
          backgroundColor: "#d43526"
        }
      ]
    };
  }, [stats]);

  const chartTopComponentsData = useMemo(() => {
    if (!stats) return null;
    return {
      labels: stats.top_5_composants.map((item) => item.composant__reference),
      datasets: [
        {
          data: stats.top_5_composants.map((item) => item.total),
          backgroundColor: ["#d43526", "#0d6efd", "#20c997", "#fd7e14", "#6f42c1"]
        }
      ]
    };
  }, [stats]);

  return (
    <Layout title="Dashboard Service 3PH">
      <div className="row g-3 mb-3">
        <div className="col-lg-7">
          <div className="card h-100">
            <div className="card-header">Statistiques globales</div>
            <div className="card-body">
              {stats && (
                <>
                  <p className="mb-2">
                    Delai moyen de traitement: <strong>{stats.delai_moyen_traitement_heures} h</strong>
                  </p>
                  {chartStatusData && <Bar data={chartStatusData} />}
                </>
              )}
            </div>
          </div>
        </div>
        <div className="col-lg-5">
          <div className="card h-100">
            <div className="card-header">Top composants demandes</div>
            <div className="card-body">{chartTopComponentsData && <Pie data={chartTopComponentsData} />}</div>
          </div>
        </div>
      </div>

      <div className="card mb-3">
        <div className="card-header d-flex justify-content-between">
          <span>Gestion encadrants</span>
          <div className="d-flex gap-2">
            <button className="btn btn-sm btn-outline-primary" onClick={() => downloadReport("csv")}>
              Export CSV
            </button>
            <button className="btn btn-sm btn-outline-danger" onClick={() => downloadReport("pdf")}>
              Export PDF
            </button>
          </div>
        </div>
        <div className="card-body border-bottom">
          <form className="row g-2" onSubmit={createEncadrant}>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Username"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Prenom"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              />
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Nom"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Departement"
                value={form.departement}
                onChange={(e) => setForm({ ...form, departement: e.target.value })}
              />
            </div>
            <div className="col-md-1">
              <input
                type="password"
                className="form-control"
                placeholder="Pass"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>
            <div className="col-md-1">
              <button className="btn btn-success w-100">+</button>
            </div>
          </form>
        </div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Departement</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {encadrants.map((e) => (
                <tr key={e.id}>
                  <td>{e.id}</td>
                  <td>{e.username}</td>
                  <td>{e.email}</td>
                  <td>{e.departement}</td>
                  <td>
                    <button className="btn btn-sm btn-outline-danger" onClick={() => deleteEncadrant(e.id)}>
                      Supprimer
                    </button>
                  </td>
                </tr>
              ))}
              {encadrants.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-muted">
                    Aucun encadrant
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Gestion etudiants</div>
        <div className="card-body border-bottom">
          <form className="row g-2" onSubmit={createStudent}>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Username"
                value={studentForm.username}
                onChange={(e) => setStudentForm({ ...studentForm, username: e.target.value })}
                required
              />
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Email"
                value={studentForm.email}
                onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })}
                required
              />
            </div>
            <div className="col-md-1">
              <input
                className="form-control"
                placeholder="Classe"
                value={studentForm.classe}
                onChange={(e) => setStudentForm({ ...studentForm, classe: e.target.value })}
              />
            </div>
            <div className="col-md-2">
              <select
                className="form-select"
                value={studentForm.encadrant}
                onChange={(e) => setStudentForm({ ...studentForm, encadrant: e.target.value })}
              >
                <option value="">Encadrant</option>
                {encadrants.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.username}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Prenom"
                value={studentForm.first_name}
                onChange={(e) => setStudentForm({ ...studentForm, first_name: e.target.value })}
              />
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Nom"
                value={studentForm.last_name}
                onChange={(e) => setStudentForm({ ...studentForm, last_name: e.target.value })}
              />
            </div>
            <div className="col-md-1">
              <input
                type="password"
                className="form-control"
                placeholder="Pass"
                value={studentForm.password}
                onChange={(e) => setStudentForm({ ...studentForm, password: e.target.value })}
              />
            </div>
            <div className="col-md-1">
              <button className="btn btn-success w-100">+</button>
            </div>
          </form>
        </div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Classe</th>
                <th>Encadrant</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {etudiants.map((e) => (
                <tr key={e.id}>
                  <td>{e.id}</td>
                  <td>{e.username}</td>
                  <td>{e.email}</td>
                  <td>{e.classe}</td>
                  <td>
                    {encadrants.find((enc) => enc.id === e.encadrant)?.username || "-"}
                  </td>
                  <td>
                    <button className="btn btn-sm btn-outline-danger" onClick={() => deleteStudent(e.id)}>
                      Supprimer
                    </button>
                  </td>
                </tr>
              ))}
              {etudiants.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-muted">
                    Aucun etudiant
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
