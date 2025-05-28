
class CharacterHandler:

    def __init__(self, glv):
        self.glv = glv

    def characters(self, characters):
        for character in characters:
            character['matches'] = self.character(character)
        return characters

    def character(self, character):
        items = self.glv.db.find_characters(character)

        characters = {}
        for row in items:
            cid, eid, romanji, title = row
            if cid not in characters:
                if eid and (romanji or title):  # only add if we have an entry id and either romanji or title
                    title = romanji if romanji != '' else title
                    characters[cid] = f"{eid}, {title}"
        return characters
