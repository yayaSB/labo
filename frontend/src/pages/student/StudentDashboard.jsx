import { useEffect, useState } from "react";
import api from "../../api/client";
import Layout from "../../components/Layout";

const statusLabels = {
  en_attente_encadrant: "En attente encadrant",
  en_attente_labo: "En attente labo",
  en_attente_achat: "En attente achat",
  approuvee: "Approuvee",
  refusee: "Refusee",
  terminee: "Terminee"
};

export default function StudentDashboard() {
  const [composants, setComposants] = useState([]);
  const [demandes, setDemandes] = useState([]);
  const [composantId, setComposantId] = useState("");
  const [quantite, setQuantite] = useState(1);

  const loadData = async () => {
    const [cRes, dRes] = await Promise.all([
      api.get("/composants"),
      api.get("/mes-demandes")
    ]);
    setComposants(cRes.data);
    setDemandes(dRes.data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const createDemande = async (event) => {
    event.preventDefault();
    await api.post("/demandes", { composant_id: Number(composantId), quantite: Number(quantite) });
    setComposantId("");
    setQuantite(1);
    loadData();
  };

  const cancelDemande = async (id) => {
    await api.delete(`/demande/${id}`);
    loadData();
  };

  return (
    <Layout title="Dashboard Etudiant">
      <div className="card mb-3">
        <div className="card-header">Nouvelle demande</div>
        <div className="card-body">
          <form className="row g-2" onSubmit={createDemande}>
            <div className="col-md-6">
              <select
                className="form-select"
                value={composantId}
                onChange={(e) => setComposantId(e.target.value)}
                required
              >
                <option value="">Choisir un composant</option>
                {composants.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nom} ({c.reference}) - stock: {c.quantite_disponible}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-3">
              <input
                type="number"
                min={1}
                className="form-control"
                value={quantite}
                onChange={(e) => setQuantite(e.target.value)}
              />
            </div>
            <div className="col-md-3">
              <button className="btn btn-primary w-100">Soumettre</button>
            </div>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Mes demandes</div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>ID</th>
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
                  <td>
                    {d.composant_nom} ({d.composant_reference})
                  </td>
                  <td>{d.quantite}</td>
                  <td>{statusLabels[d.statut] || d.statut}</td>
                  <td>
                    {d.statut === "en_attente_encadrant" && (
                      <button className="btn btn-sm btn-outline-danger" onClick={() => cancelDemande(d.id)}>
                        Annuler
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {demandes.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-muted">
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
