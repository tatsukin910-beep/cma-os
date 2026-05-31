Import streamlit as st
import random
import time
import hashlib
from dataclasses import dataclass


# =========================
# 🧠 CMA STATE
# =========================
@dataclass
class CMAState:
    event: float = 0.0
    emotion: float = 0.0
    structure: float = 0.0
    system: float = 0.0


# =========================
# 🧠 COGNITIVE + CMA ENGINE
# =========================
class CognitiveCMAOS:

    def __init__(self, stress=0.3, seed_text=""):
        self.stress = stress
        self.loops = 0
        self.seed = int(hashlib.md5(seed_text.encode()).hexdigest(), 16) % 10000
        self.rng = random.Random(self.seed)

        # internal state
        self.rumination = 0.2
        self.uncertainty = 0.5
        self.clarity = 0.5

    # -------------------------
    # risk model
    # -------------------------
    def calc_risk(self, event: str):

        triggers = ["気持ち", "返信", "本音", "不安", "どうしよう"]
        hit = sum(w in event for w in triggers)

        base = 0.25 + min(hit * 0.2, 0.6)

        risk = base
        risk *= (1 + self.stress * 0.6)
        risk *= (1 + self.loops * 0.1)

        noise = self.rng.uniform(-0.05, 0.05)

        return max(0.0, min(1.0, risk + noise))

    # -------------------------
    # internal update
    # -------------------------
    def update_internal(self, risk):

        if risk < 0.3:
            self.clarity += 0.15
            self.uncertainty -= 0.1
            self.rumination -= 0.05

        elif risk > 0.7:
            self.clarity -= 0.1
            self.uncertainty += 0.15
            self.rumination += 0.1

        self.clarity = max(0, min(1, self.clarity))
        self.uncertainty = max(0, min(1, self.uncertainty))
        self.rumination = max(0, min(1, self.rumination))

    # -------------------------
    # CMA mapping
    # -------------------------
    def to_cma(self, event: str, risk: float):

        trigger = sum(w in event for w in ["不安", "返信", "気持ち", "本音", "どうしよう"])

        cma = CMAState()

        # Event layer
        cma.event = min(1.0, 0.3 + trigger * 0.2)

        # Emotion layer
        cma.emotion = min(1.0, risk * 0.8 + self.stress * 0.4)

        # Structure layer
        cma.structure = min(
            1.0,
            (self.rumination * 0.5) + (self.uncertainty * 0.5)
        )

        # System layer
        cma.system = min(
            1.0,
            (cma.emotion * 0.4) +
            (cma.structure * 0.4) +
            (self.loops * 0.1)
        )

        return cma

    # -------------------------
    # decision engine
    # -------------------------
    def decide(self, cma):

        if cma.system > 0.85:
            return "EMERGENCY"

        if cma.structure > 0.7:
            return "AVOID DECISION"

        if cma.emotion < 0.4 and cma.system < 0.6:
            return "OK"

        return "PROCESS"

    # -------------------------
    # step
    # -------------------------
    def step(self, event):

        self.loops += 1

        risk = self.calc_risk(event)
        self.update_internal(risk)
        cma = self.to_cma(event, risk)
        decision = self.decide(cma)

        return {
            "loop": self.loops,
            "risk": round(risk, 3),
            "cma": {
                "event": round(cma.event, 3),
                "emotion": round(cma.emotion, 3),
                "structure": round(cma.structure, 3),
                "system": round(cma.system, 3),
            },
            "internal": {
                "clarity": round(self.clarity, 3),
                "uncertainty": round(self.uncertainty, 3),
                "rumination": round(self.rumination, 3),
            },
            "decision": decision
        }

    # -------------------------
    # run
    # -------------------------
    def run(self, event, max_loops=3):

        logs = []

        for _ in range(max_loops):
            r = self.step(event)
            logs.append(r)

            if r["decision"] != "PROCESS":
                break

        final = logs[-1]["decision"]

        if final == "EMERGENCY":
            return "⚠️ EMERGENCY → 思考停止推奨", logs
        elif final == "AVOID DECISION":
            return "🟡 保留推奨 → 判断遅延状態", logs
        else:
            return "✅ OK → 軽い判断OK", logs


# =========================
# 🖥️ STREAMLIT UI
# =========================
def main():

    st.set_page_config(page_title="Cognitive CMA OS", page_icon="🧠")
    st.title("🧠 Cognitive CMA OS")
    st.markdown("---")

    stress = st.sidebar.slider("stress", 0.0, 1.0, 0.3)

    event = st.text_input("イベント入力", "返信が来ない")

    if st.button("▶ 実行"):

        os = CognitiveCMAOS(stress=stress, seed_text=event)

        with st.status("processing...", expanded=True):

            result, logs = os.run(event)

            time.sleep(0.5)

            for l in logs:
                st.write("----")
                st.write(f"loop: {l['loop']}")
                st.write(f"risk: {l['risk']}")
                st.write(f"decision: {l['decision']}")

                st.write("CMA:")
                st.write(l["cma"])

                st.write("internal:")
                st.write(l["internal"])

        st.subheader("🧠 RESULT")

        if "EMERGENCY" in result:
            st.error(result)
        elif "保留" in result:
            st.warning(result)
        else:
            st.success(result)

    # panic
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🛑 Panic Reset"):
            st.rerun()

    with col2:
        if st.button("🔄 Reset"):
            st.rerun()


if __name__ == "__main__":
    main()