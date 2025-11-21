const adminPkg = require("firebase-admin");

const ORIGIN = "https://www.alexsjsju.eu"; 

function setCorsHeaders(res) {
  res.setHeader("Access-Control-Allow-Origin", ORIGIN);
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader(
    "Access-Control-Allow-Headers",
    "Content-Type, Authorization, X-Requested-With"
  );
}

if (!global.__firebaseAdminInitialized) {
  const saString = process.env.FIREBASE_SERVICE_ACCOUNT;
  if (!saString) {
    console.warn("FIREBASE_SERVICE_ACCOUNT non impostata nelle env vars.");
  } else {
    try {
      const serviceAccount = JSON.parse(saString);
      adminPkg.initializeApp({
        credential: adminPkg.credential.cert(serviceAccount),
      });
      global.__firebaseAdminInitialized = true;
      console.log("Firebase Admin inizializzato.");
    } catch (err) {
      console.error("Errore parsing FIREBASE_SERVICE_ACCOUNT:", err);
    }
  }
}

const admin = adminPkg.apps.length ? adminPkg : null;

module.exports = async (req, res) => {
  setCorsHeaders(res);

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  try {
    if (!admin || !admin.apps.length) {
      return res.status(500).json({ error: "Firebase non inizializzato" });
    }
    const db = admin.firestore();

    if (req.method === "GET") {
      const snap = await db
        .collection("memorie")
        .orderBy("createdAt", "desc")
        .limit(10)
        .get();

      const items = snap.docs.map(d => ({ id: d.id, ...d.data() }));
      return res.status(200).json({ ok: true, items });
    }

    if (req.method === "POST") {
      const body = req.body || (await new Promise(r => {
        let s = "";
        req.on("data", c => s += c);
        req.on("end", () => r(JSON.parse(s || "{}")));
      }));

      const doc = {
        tipo: body.tipo || "generica",
        testo: body.testo || "",
        createdAt: admin.firestore.FieldValue.serverTimestamp()
      };

      const ref = await db.collection("memorie").add(doc);
      return res.status(201).json({ ok: true, id: ref.id });
    }

    return res.status(405).json({ error: "Method not allowed" });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Server error", details: String(err) });
  }
};
