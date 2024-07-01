from ndn.encoding import ModelField, NameField, RepeatedField, TlvModel


class AddMessage(TlvModel):
    publisher_name = NameField(0x16a)
    hosting_as_list = RepeatedField(NameField())


class RemoveMessage(TlvModel):
    publisher_name = NameField(0x16a)
    hosting_as_list = RepeatedField(NameField())


class SetMessage(TlvModel):
    publisher_name = NameField(0x16a)
    hosting_as_list = RepeatedField(NameField())


class GetMessage(TlvModel):
    publisher_name = NameField(0x16a)


class GetLpmMessage(TlvModel):
    publisher_name = NameField(0x16a)


class PnpIMessage(TlvModel):
    add_message = ModelField(0x16b, AddMessage)  # Val2  = 2 TLV-LENGTH Inner
    remove_message = ModelField(0x16c, RemoveMessage)  # Val2  = 2 TLV-LENGTH Inner
    set_message = ModelField(0x16d, SetMessage)  # Val2  = 2 TLV-LENGTH Inner
    get_message = ModelField(0x16e, GetMessage)  # Val2  = 2 TLV-LENGTH Inner
    getlpm_message = ModelField(0x16f, GetLpmMessage)


class PnpDMessage(TlvModel):
    publisher_name = NameField(0x16a)
    hosting_as_list = RepeatedField(NameField())
