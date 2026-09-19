# DiffusionDrive navtest 失败类型学报告
总场景 12147, PDMS 0.8807

## 一、按扣分签名归类(可重叠)
- 碰撞 (NC<1): 225 场景 (1.85%)
- 驶出路面 (DAC<1): 458 场景 (3.77%)
- 跟车过近 (TTC<1): 636 场景 (5.24%)
- 停滞/蠕行 (EP<0.5): 733 场景 (6.03%)
- 逆行 (DDC<1): 343 场景 (2.82%)
- 多项硬失败 (≥2项): 248 场景 (2.04%)
- 完全 0 分: 656 场景 (5.40%)

## 二、各类代表场景(供人工看图确认)
### collision
- 01d061d9a66451ea  score=0.000 NC=0.00 DAC=1.00 TTC=0.00 EP=0.00
- 35f226ec4cac52fc  score=0.000 NC=0.00 DAC=1.00 TTC=0.00 EP=0.00
- 63b91b18f46a5a96  score=0.000 NC=0.00 DAC=1.00 TTC=0.00 EP=0.00
### offroad
- fb643a2514195bfa  score=0.000 NC=1.00 DAC=0.00 TTC=1.00 EP=0.00
- 4a919f7ea2f65200  score=0.000 NC=1.00 DAC=0.00 TTC=1.00 EP=0.00
- 2aade0b3987d5366  score=0.000 NC=1.00 DAC=0.00 TTC=0.00 EP=0.00
### closefollow
- da928b52410d5da6  score=0.289 NC=1.00 DAC=1.00 TTC=0.00 EP=0.29
- 1fe5f6af95e15489  score=0.397 NC=1.00 DAC=1.00 TTC=0.00 EP=0.55
- 624b5f7f1f4a503e  score=0.404 NC=1.00 DAC=1.00 TTC=0.00 EP=0.57
### stagnation
- fb643a2514195bfa  score=0.000 NC=1.00 DAC=0.00 TTC=1.00 EP=0.00
- 4a919f7ea2f65200  score=0.000 NC=1.00 DAC=0.00 TTC=1.00 EP=0.00
- 2aade0b3987d5366  score=0.000 NC=1.00 DAC=0.00 TTC=0.00 EP=0.00