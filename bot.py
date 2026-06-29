import os
import logging
import random
import colorsys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import io
from PIL import Image, ImageDraw

# ============= LOGGING SETUP =============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= ENVIRONMENT VARIABLES =============
BOT_TOKEN = os.environ.get('BOT_TOKEN')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'ColorStudio1Bot')
BOT_NAME = os.environ.get('BOT_NAME', 'ColorStudio1Bot')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable is not set!")
    raise ValueError("BOT_TOKEN is required. Add it to Railway variables.")

logger.info(f"✅ Starting {BOT_NAME} (@{BOT_USERNAME})")

# ============= COLOR FUNCTIONS =============

def hex_to_rgb(hex_color):
    """Convert HEX color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    """Convert RGB values to HEX color"""
    return f"#{r:02x}{g:02x}{b:02x}"

def generate_random_color():
    """Generate a random HEX color code"""
    return f"#{random.randint(0, 0xFFFFFF):06x}"

def generate_color_palette(count=5):
    """Generate a palette of colors"""
    base_hue = random.random()
    palette = []
    for i in range(count):
        hue = (base_hue + i * 0.15) % 1.0
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        hex_color = rgb_to_hex(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        palette.append(hex_color)
    return palette

def generate_monochromatic(base_color):
    """Generate monochromatic color scheme"""
    rgb = hex_to_rgb(base_color)
    hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    colors = []
    for i in range(5):
        brightness = max(0.1, min(1.0, (i * 0.2 + 0.2)))
        new_rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], brightness)
        colors.append(rgb_to_hex(int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255)))
    return colors

def generate_complementary(base_color):
    """Generate complementary color"""
    rgb = hex_to_rgb(base_color)
    complement = tuple(255 - value for value in rgb)
    return rgb_to_hex(complement[0], complement[1], complement[2])

def generate_triad(base_color):
    """Generate triad color scheme"""
    rgb = hex_to_rgb(base_color)
    hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    triad = []
    for i in range(3):
        hue = (hsv[0] + i/3) % 1.0
        new_rgb = colorsys.hsv_to_rgb(hue, hsv[1], hsv[2])
        triad.append(rgb_to_hex(int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255)))
    return triad

def generate_analogous(base_color):
    """Generate analogous color scheme"""
    rgb = hex_to_rgb(base_color)
    hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    analogous = []
    for i in range(-2, 3):
        hue = (hsv[0] + i * 0.05) % 1.0
        new_rgb = colorsys.hsv_to_rgb(hue, hsv[1], hsv[2])
        analogous.append(rgb_to_hex(int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255)))
    return analogous

def generate_split_complementary(base_color):
    """Generate split complementary colors"""
    rgb = hex_to_rgb(base_color)
    hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    split = []
    for i in [-1, 1]:
        hue = (hsv[0] + 0.5 + i * 0.1) % 1.0
        new_rgb = colorsys.hsv_to_rgb(hue, hsv[1], hsv[2])
        split.append(rgb_to_hex(int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255)))
    return split

def generate_tetradic(base_color):
    """Generate tetradic color scheme"""
    rgb = hex_to_rgb(base_color)
    hsv = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    tetradic = []
    for i in range(4):
        hue = (hsv[0] + i * 0.25) % 1.0
        new_rgb = colorsys.hsv_to_rgb(hue, hsv[1], hsv[2])
        tetradic.append(rgb_to_hex(int(new_rgb[0]*255), int(new_rgb[1]*255), int(new_rgb[2]*255)))
    return tetradic

def get_color_name(hex_color):
    """Get color name"""
    rgb = hex_to_rgb(hex_color)
    color_names = {
        (255,0,0): 'Red', (0,255,0): 'Green', (0,0,255): 'Blue',
        (255,255,0): 'Yellow', (0,255,255): 'Cyan', (255,0,255): 'Magenta',
        (255,255,255): 'White', (0,0,0): 'Black', (128,128,128): 'Gray',
        (255,165,0): 'Orange', (128,0,128): 'Purple', (255,192,203): 'Pink',
        (165,42,42): 'Brown', (0,128,0): 'Dark Green', (0,0,128): 'Navy',
        (255,215,0): 'Gold', (192,192,192): 'Silver', (255,20,147): 'Hot Pink',
        (255,69,0): 'Red Orange', (255,105,180): 'Light Pink', (255,140,0): 'Dark Orange',
        (0,255,255): 'Cyan', (255,255,255): 'White', (0,0,0): 'Black'
    }
    closest = min(color_names.keys(), key=lambda c: sum((c[i]-rgb[i])**2 for i in range(3)))
    return color_names.get(closest, 'Unknown')

def create_color_preview(hex_color, width=300, height=150):
    """Create a color preview image"""
    rgb = hex_to_rgb(hex_color)
    img = Image.new('RGB', (width, height), color=rgb)
    draw = ImageDraw.Draw(img)
    
    # Add border
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=3)
    
    # Add color info text
    try:
        text = hex_color.upper()
        text_color = 'white' if sum(rgb) < 384 else 'black'
        draw.text((10, height-30), text, fill=text_color)
        draw.text((10, 10), get_color_name(hex_color), fill=text_color)
    except:
        pass
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def create_palette_image(colors, width=500, height=100):
    """Create a palette image from colors"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    width_per_color = width // len(colors)
    for i, color in enumerate(colors):
        rgb = hex_to_rgb(color)
        x1 = i * width_per_color
        x2 = (i + 1) * width_per_color
        draw.rectangle([x1, 0, x2, height], fill=rgb)
        draw.rectangle([x1, 0, x2, height], outline='black', width=1)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# ============= USER DATA =============
user_data = {}

# ============= COMMAND HANDLERS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    first_name = user.first_name or "User"
    
    welcome_text = (
        f"🎨 *Welcome to {BOT_NAME}, {first_name}!*\n\n"
        f"I'm @{BOT_USERNAME}, your color studio!\n\n"
        "✨ *What I can do:*\n"
        "• Generate random colors\n"
        "• Create color palettes\n"
        "• Find complementary colors\n"
        "• Generate monochromatic schemes\n"
        "• Triad and analogous colors\n"
        "• Split complementary\n"
        "• Tetradic color schemes\n"
        "• Color information\n\n"
        "👇 *How to use:*\n"
        "• Click a button below\n"
        "• Send me a color (HEX code)\n\n"
        "📤 *Commands:*\n"
        "/random - Random color\n"
        "/palette - Color palette\n"
        "/info - Color info\n"
        "/about - About this bot"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 Random Color", callback_data="random"),
            InlineKeyboardButton("🎨 Color Palette", callback_data="palette"),
        ],
        [
            InlineKeyboardButton("💡 Complementary", callback_data="complementary"),
            InlineKeyboardButton("🌈 Monochromatic", callback_data="monochromatic"),
        ],
        [
            InlineKeyboardButton("🔺 Triad", callback_data="triad"),
            InlineKeyboardButton("📊 Analogous", callback_data="analogous"),
        ],
        [
            InlineKeyboardButton("✂️ Split Complementary", callback_data="split"),
            InlineKeyboardButton("🔲 Tetradic", callback_data="tetradic"),
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about_text = (
        "ℹ️ *About ColorStudioBot*\n\n"
        "🎨 Professional Color Generator Bot\n\n"
        "✨ *Features:*\n"
        "• Random color generation\n"
        "• Color palettes\n"
        "• Complementary colors\n"
        "• Monochromatic schemes\n"
        "• Triad colors\n"
        "• Analogous colors\n"
        "• Split complementary\n"
        "• Tetradic schemes\n"
        "• Color information\n\n"
        "📝 *How to use HEX codes:*\n"
        "Send #FF0000 for Red\n"
        "Send #00FF00 for Green\n"
        "Send #0000FF for Blue\n\n"
        "Made with ❤️ using Python"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        about_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def random_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /random command."""
    hex_color = generate_random_color()
    rgb = hex_to_rgb(hex_color)
    color_name = get_color_name(hex_color)
    
    # Create color preview
    preview = create_color_preview(hex_color)
    
    response = (
        f"🎲 *Random Color*\n\n"
        f"🎨 Color: `{hex_color.upper()}`\n"
        f"🔴 RGB: ({rgb[0]}, {rgb[1]}, {rgb[2]})\n"
        f"📝 Name: *{color_name}*\n\n"
        f"💡 Send me a HEX code to learn more!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 Another Color", callback_data="random"),
            InlineKeyboardButton("🎨 Palette", callback_data="palette"),
        ],
        [
            InlineKeyboardButton("🔙 Menu", callback_data="menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=preview,
        caption=response,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def palette_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /palette command."""
    palette = generate_color_palette()
    
    response = "🎨 *Color Palette*\n\n"
    for color in palette:
        response += f"• `{color.upper()}`\n"
    
    # Create palette image
    img = create_palette_image(palette)
    
    response += "\n💡 Each color is harmonious with the others!"
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 New Palette", callback_data="palette"),
            InlineKeyboardButton("🎨 Random Color", callback_data="random"),
        ],
        [
            InlineKeyboardButton("🔙 Menu", callback_data="menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=img,
        caption=response,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command."""
    await update.message.reply_text(
        "🔍 *Color Information*\n\n"
        "Send me a HEX color code!\n"
        "Example: `#FF0000` for Red\n\n"
        "Format: `#RRGGBB`",
        parse_mode='Markdown'
    )


async def handle_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle color text input."""
    text = update.message.text.strip()
    
    # Check if it's a HEX color
    if not text.startswith('#'):
        await update.message.reply_text(
            "❌ Please send a valid HEX color code!\n"
            "Example: `#FF0000` for Red",
            parse_mode='Markdown'
        )
        return
    
    try:
        hex_color = text.upper()
        rgb = hex_to_rgb(hex_color)
        color_name = get_color_name(hex_color)
        
        # Generate color schemes
        complementary = generate_complementary(hex_color)
        monochromatic = generate_monochromatic(hex_color)
        triad = generate_triad(hex_color)
        analogous = generate_analogous(hex_color)
        split = generate_split_complementary(hex_color)
        tetradic = generate_tetradic(hex_color)
        
        # Create preview
        preview = create_color_preview(hex_color)
        
        response = (
            f"🎨 *Color Information*\n\n"
            f"📝 Color: `{hex_color}`\n"
            f"🔴 RGB: ({rgb[0]}, {rgb[1]}, {rgb[2]})\n"
            f"📊 Name: *{color_name}*\n\n"
            f"✨ *Color Schemes:*\n"
            f"🔄 Complementary: `{complementary}`\n"
            f"🌈 Monochromatic: `{', '.join(monochromatic)}`\n"
            f"🔺 Triad: `{', '.join(triad)}`\n"
            f"📊 Analogous: `{', '.join(analogous)}`\n"
            f"✂️ Split Complementary: `{', '.join(split)}`\n"
            f"🔲 Tetradic: `{', '.join(tetradic)}`\n\n"
            f"💡 Try these colors in your designs!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🎲 Random Color", callback_data="random"),
                InlineKeyboardButton("🎨 Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=preview,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error processing color: {e}")
        await update.message.reply_text(
            "❌ Invalid color format!\n"
            "Please use format: `#RRGGBB`\n"
            "Example: `#FF0000`",
            parse_mode='Markdown'
        )


# ============= CALLBACK QUERY HANDLERS =============

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # ===== MENU =====
    if data == "menu":
        keyboard = [
            [
                InlineKeyboardButton("🎲 Random Color", callback_data="random"),
                InlineKeyboardButton("🎨 Color Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("💡 Complementary", callback_data="complementary"),
                InlineKeyboardButton("🌈 Monochromatic", callback_data="monochromatic"),
            ],
            [
                InlineKeyboardButton("🔺 Triad", callback_data="triad"),
                InlineKeyboardButton("📊 Analogous", callback_data="analogous"),
            ],
            [
                InlineKeyboardButton("✂️ Split Complementary", callback_data="split"),
                InlineKeyboardButton("🔲 Tetradic", callback_data="tetradic"),
            ],
            [
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🎨 *Welcome to ColorStudioBot!*\n\nWhat would you like to do?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== RANDOM =====
    elif data == "random":
        hex_color = generate_random_color()
        rgb = hex_to_rgb(hex_color)
        color_name = get_color_name(hex_color)
        
        preview = create_color_preview(hex_color)
        
        response = (
            f"🎲 *Random Color*\n\n"
            f"🎨 Color: `{hex_color.upper()}`\n"
            f"🔴 RGB: ({rgb[0]}, {rgb[1]}, {rgb[2]})\n"
            f"📝 Name: *{color_name}*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🎲 Another Color", callback_data="random"),
                InlineKeyboardButton("🎨 Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.delete_message()
        await query.message.reply_photo(
            photo=preview,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== PALETTE =====
    elif data == "palette":
        palette = generate_color_palette()
        
        response = "🎨 *Color Palette*\n\n"
        for color in palette:
            response += f"• `{color.upper()}`\n"
        
        img = create_palette_image(palette)
        
        keyboard = [
            [
                InlineKeyboardButton("🎲 New Palette", callback_data="palette"),
                InlineKeyboardButton("🎨 Random Color", callback_data="random"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.delete_message()
        await query.message.reply_photo(
            photo=img,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== COMPLEMENTARY =====
    elif data == "complementary":
        base = generate_random_color()
        comp = generate_complementary(base)
        
        # Create preview
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 200, 200], fill=hex_to_rgb(base))
        draw.rectangle([200, 0, 400, 200], fill=hex_to_rgb(comp))
        draw.rectangle([0, 0, 399, 199], outline='black', width=2)
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        response = (
            f"💡 *Complementary Colors*\n\n"
            f"Base: `{base.upper()}`\n"
            f"Complement: `{comp.upper()}`\n\n"
            f"Complementary colors are opposite on the color wheel!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 New Pair", callback_data="complementary"),
                InlineKeyboardButton("🎨 Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.delete_message()
        await query.message.reply_photo(
            photo=img_byte_arr,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== MONOCHROMATIC =====
    elif data == "monochromatic":
        base = generate_random_color()
        mono_colors = generate_monochromatic(base)
        
        img = create_palette_image(mono_colors)
        
        response = f"🌈 *Monochromatic Scheme*\n\nBase: `{base.upper()}`\n\nVarying brightness of the same color!"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 New Scheme", callback_data="monochromatic"),
                InlineKeyboardButton("🎨 Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.delete_message()
        await query.message.reply_photo(
            photo=img,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== TRIAD =====
    elif data == "triad":
        base = generate_random_color()
        triad_colors = generate_triad(base)
        
        img = create_palette_image(triad_colors)
        
        response = f"🔺 *Triad Color Scheme*\n\nBase: `{base.upper()}`\n\nThree colors evenly spaced on the color wheel!"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 New Triad", callback_data="triad"),
                InlineKeyboardButton("🎨 Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.delete_message()
        await query.message.reply_photo(
            photo=img,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== ANALOGOUS =====
    elif data == "analogous":
        base = generate_random_color()
        analog_colors = generate_analogous(base)
        
        img = create_palette_image(analog_colors)
        
        response = f"📊 *Analogous Color Scheme*\n\nBase: `{base.upper()}`\n\nColors adjacent on the color wheel!"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 New Scheme", callback_data="analogous"),
                InlineKeyboardButton("🎨 Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.delete_message()
        await query.message.reply_photo(
            photo=img,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== SPLIT COMPLEMENTARY =====
    elif data == "split":
        base = generate_random_color()
        split_colors = generate_split_complementary(base)
        
        # Create preview with base + split colors
        all_colors = [base] + split_colors
        img = create_palette_image(all_colors)
        
        response = (
            f"✂️ *Split Complementary Scheme*\n\n"
            f"Base: `{base.upper()}`\n"
            f"Split: `{', '.join(split_colors)}`\n\n"
            f"Base color with two colors adjacent to its complement!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 New Scheme", callback_data="split"),
                InlineKeyboardButton("🎨 Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.delete_message()
        await query.message.reply_photo(
            photo=img,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== TETRADIC =====
    elif data == "tetradic":
        base = generate_random_color()
        tetradic_colors = generate_tetradic(base)
        
        img = create_palette_image(tetradic_colors)
        
        response = (
            f"🔲 *Tetradic Color Scheme*\n\n"
            f"Base: `{base.upper()}`\n"
            f"Colors: `{', '.join(tetradic_colors)}`\n\n"
            f"Four colors with two complementary pairs!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 New Scheme", callback_data="tetradic"),
                InlineKeyboardButton("🎨 Palette", callback_data="palette"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.delete_message()
        await query.message.reply_photo(
            photo=img,
            caption=response,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== ABOUT =====
    elif data == "about":
        about_text = (
            "ℹ️ *About ColorStudioBot*\n\n"
            "🎨 Professional Color Generator Bot\n\n"
            "✨ *Features:*\n"
            "• Random color generation\n"
            "• Color palettes\n"
            "• Complementary colors\n"
            "• Monochromatic schemes\n"
            "• Triad colors\n"
            "• Analogous colors\n"
            "• Split complementary\n"
            "• Tetradic schemes\n\n"
            "Made with ❤️ using Python"
        )
        keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            about_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


def main():
    """Start the bot."""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("about", about))
        application.add_handler(CommandHandler("random", random_color))
        application.add_handler(CommandHandler("palette", palette_command))
        application.add_handler(CommandHandler("info", info_command))
        
        # Callback handler
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Message handler for text (color codes)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_color))
        
        logger.info("🚀 Bot started successfully!")
        logger.info(f"📱 Bot username: @{BOT_USERNAME}")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()
