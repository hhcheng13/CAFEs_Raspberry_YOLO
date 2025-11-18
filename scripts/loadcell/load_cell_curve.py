import numpy as np
import matplotlib.pyplot as plt

# === Your calibration data ===
raws = np.array([
    600974, 618508, 633737, 656763, 671978, 693392, 708632, 716307, 731464, 746480,
    754343, 769677, 784819, 792470, 807809, 823013, 831331, 846575, 862080, 884730,
    899958, 906214, 922063, 937275, 960418, 975661, 983407, 998743, 1013568, 1051442,
    1059128, 1074471, 1097371, 1113103, 1128133, 1135081, 1150370, 1165450, 1203965,
    1213392, 1228098, 1242513, 1281140, 1288015, 1302843, 1317281, 1355577
], dtype=float)

weights = np.array([
    0, 20, 40, 70, 90, 120, 140, 150, 170, 190,
    200, 220, 240, 250, 270, 290, 300, 320, 340, 370,
    390, 400, 420, 440, 470, 490, 500, 520, 540, 590,
    600, 620, 650, 670, 690, 700, 720, 740, 790,
    800, 820, 840, 890, 900, 920, 940, 990
], dtype=float)

# === Fitted model from your calibration result ===
a = 0.0013129310  # grams per count
b = -790.910827

# Predicted weights using the fit
fit_weights = a * raws + b

# Compute residuals
residuals = weights - fit_weights

# === Plot 1: Calibration fit ===
plt.figure(figsize=(8, 6))
plt.scatter(raws, weights, color='blue', label='Measured points')
plt.plot(raws, fit_weights, 'r-', label='Linear fit')
plt.title('HX711 Load Cell Calibration')
plt.xlabel('Raw reading (ADC counts)')
plt.ylabel('Weight (g)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)

# === Plot 2: Residuals ===
plt.figure(figsize=(8, 3))
plt.scatter(raws, residuals, color='purple')
plt.axhline(0, color='black', linestyle='--', linewidth=1)
plt.title('Residuals (Measured - Fitted)')
plt.xlabel('Raw reading (ADC counts)')
plt.ylabel('Error (g)')
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()


# ===== Calibration Result =====
# Linear model:  weight[g] = a*raw + b   a=0.0013129310   b=-790.910827
# scale (counts per gram): 761.654602
# offset (ADC counts):     602400.9

# Paste these into your project (e.g., in setup()):
#   scale.set_scale(761.654602);
#   scale.set_offset(602400.9);

# Fit quality:
#   RMSE (grams): 0.809
#   R^2: 0.99999

# Tip: Alternatively, you can only set_scale(...) and then call tare() at 0 g.
# Done. You can keep adding points and type 'done' again to refine.
