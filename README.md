# 使用上の注意

## permissionについて
volume mountしているので、docker上で作成したlerobotの権限がrootになおり、ホストのVScodeから編集できないので、コンテナ実行時にホストのubuntuからpermissionを変更する。
```
sudo chown -R $USER:$USER /home/nomut/pi0/
```
## debugger
hostのwslのdebuggerが使えるようしてあるので、VSCodeの拡張機能で以下のコードでdebuggerがattachできる。
```
if os.environ.get("DEBUG") == "1":
    import debugpy
    print("Waiting for debugger attach on port 5678...")
    debugpy.listen(("0.0.0.0", 5678))
    debugpy.wait_for_client()
    print("Debugger attached!")
```
