from PIL import Image, ImageDraw

# === Cria base azul escuro ===
img = Image.new("RGBA", (256, 256), "#1E3A8A")  # Fundo principal
draw = ImageDraw.Draw(img)

# === Cria degradê azul suave (efeito de brilho premium) ===
gradient = Image.new("RGBA", (256, 256))
grad_draw = ImageDraw.Draw(gradient)
for y in range(128):
    # Mistura de branco e azul claro (reflexo no topo)
    opacity = int(160 - y * 1.4)
    color = (173, 216, 230, opacity)  # Azul claro (RGB + transparência)
    grad_draw.line((0, y, 256, y), fill=color)
img.alpha_composite(gradient)

# === Bordas externas suaves ===
draw.ellipse([8, 8, 248, 248], outline="#0A1E63", width=5)

# === Gráfico de barras central ===
base_y = 200
bar_width = 35
space = 20
x_start = 60
bar_heights = [70, 110, 150]

for i, h in enumerate(bar_heights):
    x0 = x_start + i * (bar_width + space)
    y0 = base_y - h
    x1 = x0 + bar_width
    y1 = base_y
    draw.rounded_rectangle([x0, y0, x1, y1], radius=6, fill="white")

# === Salva ícone em múltiplos tamanhos ===
img.save(
    "icone_gestao_moderno.ico",
    format="ICO",
    sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)]
)

print("✅ Ícone 'icone_gestao_moderno.ico' criado com brilho azul degradê premium!")
