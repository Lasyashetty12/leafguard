Put extra test images here (this folder is NOT pushed to GitHub):

data/ood/*.jpg       20+ photos that are NOT leaves (mug, hand, keyboard, floor, face, bag...)
data/healthy/*.jpg   10+ photos of HEALTHY leaves (our YOLO model has no healthy class,
                     so these test the "no disease found" answer and the sick-table trick)

For calibration and the stress test, point the scripts at your Roboflow / YOLO dataset
folders directly (they contain images/ and labels/):

  python scripts/calibrate.py   --val_dir  C:\path\to\dataset\valid
  python scripts/stress_test.py --test_dir C:\path\to\dataset\test --ood_dir data\ood --healthy_dir data\healthy
