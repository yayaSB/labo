import { useEffect, useState } from "react";
import api from "../../api/client";
import Layout from "../../components/Layout";

export default function TeacherDashboard() {
  const [demandes, setDemandes] = useState([]);

  const loadDemandes = async () => {
    const response = await api.get("/demandes/classe");
    setDemandes(response.data);
  };

  useEffect(() => {
    loadDemandes();
  }, []);

  const decision = async (id, approve) => {
    const commentaire = window.prompt("Commentaire encadrant (optionnel):", "") || "";
    const endpoint = approve
      ? `/demande/${id}/valider-encadrant`
      : `/demande/${id}/refuser-encadrant`;
    await api.put(endpoint, { commentaire_encadrant: commentaire });
    loadDemandes();
  };

  return (
    <Layout title="Dashboard Encadrant">
      <div className="card">
        <div className="card-header">Demandes de ma classe</div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>ID</th>
                <th>Etudiant</th>
                <th>Composant</th>
                <th>Quantite</th>
                <th>Statut</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {demandes.map((d) => (
                <tr key={d.id}>
                  <td>#{d.id}</td>
                  <td>{d.etudiant_nom}</td>
                  <td>
                    {d.composant_nom} ({d.composant_reference})
                  </td>
                  <td>{d.quantite}</td>
                  <td>{d.statut}</td>
                  <td className="d-flex gap-2">
                    {d.statut === "en_attente_encadrant" && (
                      <>
                        <button className="btn btn-sm btn-success" onClick={() => decision(d.id, true)}>
                          Valider
                        </button>
                        <button className="btn btn-sm btn-danger" onClick={() => decision(d.id, false)}>
                          Refuser
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {demandes.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-muted">
                    Aucune demande
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
