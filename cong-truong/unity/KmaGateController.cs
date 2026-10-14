using System.Collections.Generic;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

/// <summary>
/// Opens / closes the KMA gate leaves (KMA_Gate_{L|C|R}_{Left|Right}).
/// Attach to the imported KMA_Gate root. Each leaf's pivot is on its hinge (set up in Blender),
/// and the swing direction is detected automatically so leaves always open into the campus.
/// </summary>
public class KmaGateController : MonoBehaviour
{
    [Header("Swing")]
    [Tooltip("How far each leaf swings open, in degrees.")]
    public float openAngle = 80f;
    [Tooltip("Swing speed in degrees per second.")]
    public float swingSpeed = 70f;
    [Tooltip("Open every gate when the scene starts.")]
    public bool startOpen = false;

    [Header("Interaction")]
    [Tooltip("Player transform. If set, the key only toggles the gate nearest to the player.")]
    public Transform player;
    public float interactDistance = 4f;
#if ENABLE_INPUT_SYSTEM
    public Key toggleKey = Key.E;
#else
    public KeyCode toggleKey = KeyCode.E;
#endif
    [Tooltip("Open automatically when the player comes within autoOpenDistance, close when they leave.")]
    public bool autoOpen = false;
    public float autoOpenDistance = 6f;

    [Header("Physics")]
    [Tooltip("Adds a BoxCollider to each leaf so the player cannot walk through it.")]
    public bool addLeafColliders = true;

    class Leaf
    {
        public Transform t;
        public string gateId;   // L, C or R
        public Quaternion closedRot;
        public Quaternion openRot;
    }

    readonly List<Leaf> leaves = new List<Leaf>();
    readonly Dictionary<string, bool> gateOpen = new Dictionary<string, bool>();

    void Awake()
    {
        Vector3 inside = FindInsidePoint();
        foreach (Transform t in GetComponentsInChildren<Transform>(true))
        {
            // KMA_Gate_C_Left -> id "C"
            string[] parts = t.name.Split('_');
            if (parts.Length < 4 || parts[0] != "KMA" || parts[1] != "Gate") continue;
            if (!t.name.EndsWith("_Left") && !t.name.EndsWith("_Right")) continue;
            var r = t.GetComponent<Renderer>();
            if (r == null) continue;

            var leaf = new Leaf { t = t, gateId = parts[2], closedRot = t.rotation };
            Vector3 hinge = t.position;
            Vector3 arm = r.bounds.center - hinge;
            Quaternion plus = Quaternion.AngleAxis(openAngle, Vector3.up);
            Quaternion minus = Quaternion.AngleAxis(-openAngle, Vector3.up);
            float dPlus = Flat(hinge + plus * arm - inside).sqrMagnitude;
            float dMinus = Flat(hinge + minus * arm - inside).sqrMagnitude;
            leaf.openRot = (dPlus < dMinus ? plus : minus) * leaf.closedRot;
            leaves.Add(leaf);
            gateOpen[leaf.gateId] = startOpen;

            if (addLeafColliders && t.GetComponent<Collider>() == null)
                t.gameObject.AddComponent<BoxCollider>();
            if (startOpen) t.rotation = leaf.openRot;
        }
        if (leaves.Count == 0)
            Debug.LogWarning("KmaGateController: no KMA_Gate_*_Left/Right leaves found under " + name);
    }

    // The gate block (KMA_Structure) sits between the street and the campus; its centre is "inside"
    // relative to the leaves, which hang on the street-side pillar row.
    Vector3 FindInsidePoint()
    {
        foreach (var r in GetComponentsInChildren<Renderer>(true))
            if (r.name == "KMA_Structure") return r.bounds.center;
        return transform.position;
    }

    static Vector3 Flat(Vector3 v) { v.y = 0f; return v; }

    void Update()
    {
        if (TogglePressed())
        {
            string id = NearestGateId(player != null ? interactDistance : float.MaxValue);
            if (id != null) Toggle(id);
        }

        if (autoOpen && player != null)
        {
            foreach (var id in new List<string>(gateOpen.Keys))
            {
                bool near = DistanceToGate(id) <= autoOpenDistance;
                if (near != gateOpen[id]) SetOpen(id, near);
            }
        }

        float step = swingSpeed * Time.deltaTime;
        foreach (var leaf in leaves)
        {
            Quaternion target = gateOpen[leaf.gateId] ? leaf.openRot : leaf.closedRot;
            leaf.t.rotation = Quaternion.RotateTowards(leaf.t.rotation, target, step);
        }
    }

    bool TogglePressed()
    {
#if ENABLE_INPUT_SYSTEM
        return Keyboard.current != null && Keyboard.current[toggleKey].wasPressedThisFrame;
#else
        return Input.GetKeyDown(toggleKey);
#endif
    }

    string NearestGateId(float maxDistance)
    {
        string best = null;
        float bestD = maxDistance;
        foreach (var id in gateOpen.Keys)
        {
            float d = DistanceToGate(id);
            if (d <= bestD) { bestD = d; best = id; }
        }
        return best;
    }

    float DistanceToGate(string id)
    {
        if (player == null) return 0f;
        Vector3 sum = Vector3.zero; int n = 0;
        foreach (var leaf in leaves)
            if (leaf.gateId == id) { sum += leaf.t.position; n++; }
        return n == 0 ? float.MaxValue : Vector3.Distance(Flat(player.position), Flat(sum / n));
    }

    // ---- public API (call from triggers, UI, quests...) ----
    public void Toggle(string gateId) => SetOpen(gateId, !IsOpen(gateId));
    public bool IsOpen(string gateId) => gateOpen.TryGetValue(gateId, out bool o) && o;
    public void SetOpen(string gateId, bool open) { if (gateOpen.ContainsKey(gateId)) gateOpen[gateId] = open; }
    public void OpenAll() { foreach (var id in new List<string>(gateOpen.Keys)) gateOpen[id] = true; }
    public void CloseAll() { foreach (var id in new List<string>(gateOpen.Keys)) gateOpen[id] = false; }
}
