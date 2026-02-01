import { useState, useEffect } from "react";
import {
  getAllVotes,
  createVote,
  updateVote,
  deleteVote,
} from "../services/votingApi";

export default function VotingManagement() {
  const [votes, setVotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingVote, setEditingVote] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    question: "",
    start_time: "",
    end_time: "",
    categories: ["", ""],
  });

  // Load all votes on mount
  useEffect(() => {
    loadVotes();
  }, []);

  const loadVotes = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllVotes();
      setVotes(data);
    } catch (err) {
      setError("Fehler beim Laden der Votings: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVote = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const categories = formData.categories
        .filter((name) => name.trim())
        .map((name) => ({ name: name.trim() }));

      if (categories.length < 2) {
        setError("Mindestens 2 Kategorien erforderlich");
        return;
      }

      await createVote({
        question: formData.question,
        start_time: formData.start_time,
        end_time: formData.end_time,
        categories,
      });

      setShowCreateForm(false);
      resetForm();
      loadVotes();
    } catch (err) {
      setError("Fehler beim Erstellen: " + err.message);
    }
  };

  const handleUpdateVote = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const categories = formData.categories
        .filter((name) => name.trim())
        .map((name) => ({ name: name.trim() }));

      if (categories.length < 2) {
        setError("Mindestens 2 Kategorien erforderlich");
        return;
      }

      await updateVote(editingVote.id, {
        question: formData.question,
        start_time: formData.start_time,
        end_time: formData.end_time,
        categories,
      });

      setEditingVote(null);
      resetForm();
      loadVotes();
    } catch (err) {
      setError("Fehler beim Aktualisieren: " + err.message);
    }
  };

  const handleDeleteVote = async (voteId) => {
    if (!confirm("Voting wirklich löschen?")) return;

    setError(null);
    try {
      await deleteVote(voteId);
      loadVotes();
    } catch (err) {
      setError("Fehler beim Löschen: " + err.message);
    }
  };

  const startEdit = (vote) => {
    setEditingVote(vote);
    setFormData({
      question: vote.question,
      start_time: formatDatetimeLocal(vote.start_time),
      end_time: formatDatetimeLocal(vote.end_time),
      categories: vote.categories.map((c) => c.name),
    });
    setShowCreateForm(false);
  };

  const startCreate = () => {
    setShowCreateForm(true);
    setEditingVote(null);
    resetForm();
  };

  const resetForm = () => {
    setFormData({
      question: "",
      start_time: "",
      end_time: "",
      categories: ["", ""],
    });
  };

  const cancelForm = () => {
    setShowCreateForm(false);
    setEditingVote(null);
    resetForm();
  };

  const addCategory = () => {
    setFormData((prev) => ({
      ...prev,
      categories: [...prev.categories, ""],
    }));
  };

  const removeCategory = (index) => {
    setFormData((prev) => ({
      ...prev,
      categories: prev.categories.filter((_, i) => i !== index),
    }));
  };

  const updateCategory = (index, value) => {
    setFormData((prev) => {
      const newCategories = [...prev.categories];
      newCategories[index] = value;
      return { ...prev, categories: newCategories };
    });
  };

  const formatDatetimeLocal = (isoString) => {
    // Convert ISO string to datetime-local format (YYYY-MM-DDTHH:mm)
    return isoString.slice(0, 16);
  };

  const formatDatetimeDisplay = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString("de-DE");
  };

  const isVoteActive = (vote) => {
    const now = new Date();
    const start = new Date(vote.start_time);
    const end = new Date(vote.end_time);
    return now >= start && now <= end;
  };

  return (
    <div style={{ padding: "20px", maxWidth: "1200px", margin: "0 auto" }}>
      <h1>Voting Management</h1>

      {error && (
        <div style={{ padding: "10px", background: "#fee", border: "1px solid #c00", marginBottom: "20px" }}>
          {error}
        </div>
      )}

      {!showCreateForm && !editingVote && (
        <div style={{ marginBottom: "20px" }}>
          <button onClick={startCreate} style={{ padding: "10px 20px", fontSize: "16px" }}>
            Neues Voting erstellen
          </button>
          <button onClick={loadVotes} style={{ padding: "10px 20px", fontSize: "16px", marginLeft: "10px" }}>
            Aktualisieren
          </button>
        </div>
      )}

      {(showCreateForm || editingVote) && (
        <div style={{ border: "1px solid #ccc", padding: "20px", marginBottom: "20px", background: "#f9f9f9" }}>
          <h2>{editingVote ? "Voting bearbeiten" : "Neues Voting erstellen"}</h2>
          <form onSubmit={editingVote ? handleUpdateVote : handleCreateVote}>
            <div style={{ marginBottom: "15px" }}>
              <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                Frage:
              </label>
              <input
                type="text"
                value={formData.question}
                onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                required
                style={{ width: "100%", padding: "8px", fontSize: "14px" }}
              />
            </div>

            <div style={{ marginBottom: "15px" }}>
              <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                Startzeit:
              </label>
              <input
                type="datetime-local"
                value={formData.start_time}
                onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                required
                style={{ padding: "8px", fontSize: "14px" }}
              />
            </div>

            <div style={{ marginBottom: "15px" }}>
              <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                Endzeit:
              </label>
              <input
                type="datetime-local"
                value={formData.end_time}
                onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                required
                style={{ padding: "8px", fontSize: "14px" }}
              />
            </div>

            <div style={{ marginBottom: "15px" }}>
              <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                Kategorien:
              </label>
              {formData.categories.map((cat, index) => (
                <div key={index} style={{ display: "flex", marginBottom: "8px", alignItems: "center" }}>
                  <input
                    type="text"
                    value={cat}
                    onChange={(e) => updateCategory(index, e.target.value)}
                    placeholder={`Kategorie ${index + 1}`}
                    style={{ flex: 1, padding: "8px", fontSize: "14px" }}
                  />
                  {formData.categories.length > 2 && (
                    <button
                      type="button"
                      onClick={() => removeCategory(index)}
                      style={{ marginLeft: "10px", padding: "8px 12px" }}
                    >
                      Entfernen
                    </button>
                  )}
                </div>
              ))}
              <button type="button" onClick={addCategory} style={{ padding: "8px 12px", marginTop: "5px" }}>
                + Kategorie hinzufügen
              </button>
            </div>

            <div style={{ marginTop: "20px" }}>
              <button type="submit" style={{ padding: "10px 20px", fontSize: "16px", marginRight: "10px" }}>
                {editingVote ? "Aktualisieren" : "Erstellen"}
              </button>
              <button type="button" onClick={cancelForm} style={{ padding: "10px 20px", fontSize: "16px" }}>
                Abbrechen
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <p>Lädt...</p>
      ) : (
        <div>
          <h2>Alle Votings ({votes.length})</h2>
          {votes.length === 0 ? (
            <p>Keine Votings gefunden.</p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "10px" }}>
              <thead>
                <tr style={{ background: "#eee" }}>
                  <th style={{ padding: "10px", border: "1px solid #ccc", textAlign: "left" }}>ID</th>
                  <th style={{ padding: "10px", border: "1px solid #ccc", textAlign: "left" }}>Frage</th>
                  <th style={{ padding: "10px", border: "1px solid #ccc", textAlign: "left" }}>Startzeit</th>
                  <th style={{ padding: "10px", border: "1px solid #ccc", textAlign: "left" }}>Endzeit</th>
                  <th style={{ padding: "10px", border: "1px solid #ccc", textAlign: "left" }}>Kategorien</th>
                  <th style={{ padding: "10px", border: "1px solid #ccc", textAlign: "left" }}>Status</th>
                  <th style={{ padding: "10px", border: "1px solid #ccc", textAlign: "left" }}>Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {votes.map((vote) => (
                  <tr key={vote.id}>
                    <td style={{ padding: "10px", border: "1px solid #ccc" }}>{vote.id}</td>
                    <td style={{ padding: "10px", border: "1px solid #ccc" }}>{vote.question}</td>
                    <td style={{ padding: "10px", border: "1px solid #ccc" }}>
                      {formatDatetimeDisplay(vote.start_time)}
                    </td>
                    <td style={{ padding: "10px", border: "1px solid #ccc" }}>
                      {formatDatetimeDisplay(vote.end_time)}
                    </td>
                    <td style={{ padding: "10px", border: "1px solid #ccc" }}>
                      {vote.categories.map((c) => c.name).join(", ")}
                    </td>
                    <td style={{ padding: "10px", border: "1px solid #ccc" }}>
                      {isVoteActive(vote) ? (
                        <span style={{ color: "green", fontWeight: "bold" }}>Aktiv</span>
                      ) : (
                        <span style={{ color: "#999" }}>Inaktiv</span>
                      )}
                    </td>
                    <td style={{ padding: "10px", border: "1px solid #ccc" }}>
                      <button
                        onClick={() => startEdit(vote)}
                        style={{ padding: "5px 10px", marginRight: "5px" }}
                      >
                        Bearbeiten
                      </button>
                      <button
                        onClick={() => handleDeleteVote(vote.id)}
                        style={{ padding: "5px 10px", background: "#c00", color: "white" }}
                      >
                        Löschen
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
