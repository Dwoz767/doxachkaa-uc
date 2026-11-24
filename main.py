
    page.add(ft.Stack([ft.Image(src="bg.png", fit=ft.ImageFit.COVER, width=1080, height=2400, opacity=0.35), ft.Container(content=content, padding=16, expand=True)], expand=True))
    refresh()

ft.app(target=main, assets_dir="assets")
