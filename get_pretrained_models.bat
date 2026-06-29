@echo off
if not exist checkpoints mkdir checkpoints
curl -L "https://ml-site.cdn-apple.com/models/depth-pro/depth_pro.pt" -o "checkpoints\depth_pro.pt"
