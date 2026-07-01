class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "7053545607"
    sudo_users = "7053545607"
    GROUP_ID = -1003659707205
    TOKEN = "7712201855:AAEEqz6uQRzWjw6fFygXiBgDMfIgjCl96x0"
    mongo_url = "mongodb+srv://HaremDBBot:ThisIsPasswordForHaremDB@haremdb.swzjngj.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL = ["https://telegra.ph/file/b925c3985f0f325e62e17.jpg", "https://telegra.ph/file/4211fb191383d895dab9d.jpg"]
    SUPPORT_CHAT = "+U5QHSCCmxvFlMDc1"
    UPDATE_CHAT = "+U5QHSCCmxvFlMDc1"
    BOT_USERNAME = "Collect_Em_AllBot"
    CHARA_CHANNEL_ID = "-1002133191051"
    api_id = "36237034"
    api_hash = "31c376a5c49eabb8426df4d1f21a5d52"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
