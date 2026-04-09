import { useEffect, useState } from "react";
import api from "../../api/client";
import Layout from "../../components/Layout";

export default function AchatDashboard() {
  const [demandes, setDemandes] = useState([]);
  const [achats, setAchats] = useState([]);

  const loadData = async () => {
    const [dRes, aRes] = await Promise.all([
      api.get("/demandes/attente-achat"),
      api.get("/achats")
    ]);
    setDemandes(dRes.data);
    setAchats(aRes.data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const createAchat = async (demande) => {
    const fournisseur = window.prompt("Fournisseur", "Fournisseur demo");
    if (!fournisseur) return;
    const quantityInput = window.prompt(
      `Quantite achetee pour ${demande.composant_nom}`,
      demande.quantite
    );
    if (!quantityInput) return;
    await api.post("/achats", {
      demande_id: demande.id,
      fournisseur,
      quantite_achetee: Number(quantityInput)
    });
    loadData();
  };

  const receptionner = async (achatId) => {
    await api.put(`/achats/${achatId}/receptionner`);
    loadData();
  };

  return (
    <Layout title="Dashboard Service Achat">
      <div className="card mb-3">
        <div className="card-header">Demandes en attente achat</div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>ID</th>
                <th>Composant</th>
                <th>Quantite</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {demandes.map((d) => (
                <tr key={d.id}>
                  <td>#{d.id}</td>
                  <td>{d.composant_nom}</td>
                  <td>{d.quantite}</td>
                  <td>
                    <button className="btn btn-sm btn-primary" onClick={() => createAchat(d)}>
                      Creer commande
                    </button>
                  </td>
                </tr>
              ))}
              {demandes.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-muted">
                    Aucune demande en attente achat
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Historique achats</div>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>ID</th>
                <th>Demande</th>
                <th>Composant</th>
                <th>Fournisseur</th>
                <th>Qte</th>
                <th>Statut</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {achats.map((a) => (
                <tr key={a.id}>
                  <td>#{a.id}</td>
                  <td>#{a.demande}</td>
                  <td>{a.composant_reference}</td>
                  <td>{a.fournisseur}</td>
                  <td>{a.quantite_achetee}</td>
                  <td>{a.statut}</td>
                  <td>
                    {a.statut === "en_cours" && (
                      <button className="btn btn-sm btn-success" onClick={() => receptionner(a.id)}>
                        Receptionner
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {achats.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-muted">
                    Aucun achat
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
