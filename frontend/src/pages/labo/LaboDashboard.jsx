import { useEffect, useState } from "react";
import api from "../../api/client";
import Layout from "../../components/Layout";

export default function LaboDashboard() {
  const [demandes, setDemandes] = useState([]);
  const [composants, setComposants] = useState([]);
  const [formData, setFormData] = useState({
    nom: "",
    reference: "",
    quantite_disponible: 0,
    seuil_alerte: 0,
    localisation: ""
  });

  const loadData = async () => {
    const [dRes, cRes] = await Promise.all([
      api.get("/demandes/attente-labo"),
      api.get("/composants")
    ]);
    setDemandes(dRes.data);
    setComposants(cRes.data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const reserver = async (id) => {
    await api.put(`/demande/${id}/reserver`);
    loadData();
  };

  const createComposant = async (event) => {
    event.preventDefault();
    await api.post("/composants", {
      ...formData,
      quantite_disponible: Number(formData.quantite_disponible),
      seuil_alerte: Number(formData.seuil_alerte)
    });
    setFormData({ nom: "", reference: "", quantite_disponible: 0, seuil_alerte: 0, localisation: "" });
    loadData();
  };

  const updateStock = async (composant) => {
    const value = window.prompt(
      `Nouvelle quantite pour ${composant.nom}`,
      composant.quantite_disponible
    );
    if (value === null) return;
    await api.put(`/composants/${composant.id}`, { quantite_disponible: Number(value) });
    loadData();
  };

  return (
    <Layout title="Dashboard Labo Temps">
      <div className="card mb-3">
        <div className="card-header">Demandes en attente labo</div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>ID</th>
                <th>Etudiant</th>
                <th>Composant</th>
                <th>Quantite</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {demandes.map((d) => (
                <tr key={d.id}>
                  <td>#{d.id}</td>
                  <td>{d.etudiant_nom}</td>
                  <td>{d.composant_nom}</td>
                  <td>{d.quantite}</td>
                  <td>
                    <button className="btn btn-sm btn-primary" onClick={() => reserver(d.id)}>
                      Reserver / traiter
                    </button>
                  </td>
                </tr>
              ))}
              {demandes.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-muted">
                    Rien a traiter
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card mb-3">
        <div className="card-header">Ajouter un composant</div>
        <div className="card-body">
          <form className="row g-2" onSubmit={createComposant}>
            <div className="col-md-3">
              <input
                className="form-control"
                placeholder="Nom"
                value={formData.nom}
                onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                required
              />
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Reference"
                value={formData.reference}
                onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                required
              />
            </div>
            <div className="col-md-2">
              <input
                type="number"
                min={0}
                className="form-control"
                placeholder="Stock"
                value={formData.quantite_disponible}
                onChange={(e) => setFormData({ ...formData, quantite_disponible: e.target.value })}
              />
            </div>
            <div className="col-md-2">
              <input
                type="number"
                min={0}
                className="form-control"
                placeholder="Seuil"
                value={formData.seuil_alerte}
                onChange={(e) => setFormData({ ...formData, seuil_alerte: e.target.value })}
              />
            </div>
            <div className="col-md-2">
              <input
                className="form-control"
                placeholder="Localisation"
                value={formData.localisation}
                onChange={(e) => setFormData({ ...formData, localisation: e.target.value })}
              />
            </div>
            <div className="col-md-1">
              <button className="btn btn-success w-100">+</button>
            </div>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Stock composants</div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Reference</th>
                <th>Stock</th>
                <th>Seuil</th>
                <th>Localisation</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {composants.map((c) => (
                <tr key={c.id}>
                  <td>{c.nom}</td>
                  <td>{c.reference}</td>
                  <td>{c.quantite_disponible}</td>
                  <td>{c.seuil_alerte}</td>
                  <td>{c.localisation}</td>
                  <td>
                    <button className="btn btn-sm btn-outline-secondary" onClick={() => updateStock(c)}>
                      Modifier stock
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
