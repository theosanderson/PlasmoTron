SCHEME_REGISTRY = [] 

def register_scheme(scheme_class):
  """This defines a decorator used to make scheme-processing enumeration simple."""
  SCHEME_REGISTRY[scheme_class.label]=scheme_class
  return scheme_class

class ProcessingScheme:
  """Meta-class for a processing scheme like 'feed-plate' or 'split plate'.""""
  def __init__(self,command_issuer, form_inputs):
    self.command_issuer = command_issuer
    self.form_inputs = form_inputs
  def pre_sequence(self):
    self.command_issuer.home()
  def post_sequence(self):
    self.command_issuer.finalise()
  def main_sequence(self):
    raise NotImplementedError
  def process(self):
    self.pre_sequence()
    self.main_sequence()
    self.post_sequence()

@register_scheme
class Feed(ProcessingSheme):
  """ Feed the plate. """
  label = "feed"
  def main_sequence(self):
    cultures = self.command_issuer.get_cultures()
    for culture in cultures:
      self.command_issuer.getTip(0)
      self.command_issuer.aspirate(
          0,
          'CulturePlate',
          feedVolume + extraRemoval,
          culture['Row'],
          culture['Column'],
          plateid=request.form['plateid'])
      self.command_issuer.dropTip(0)
    self.command_issuer.getTip(0)
    for culture in cultures:

      self.command_issuer.aspirate(0, 'TubMedia', feedVolume)
      onexec = self.command_issuer.createOnExecute('feed', request.form['plateid'],
                               culture['Row'], culture['Column'])
      self.command_issuer.dispense(
          0,
          'CulturePlate',
          feedVolume,
          culture['Row'],
          culture['Column'],
          onexec,
          plateid=request.form['plateid'])

    self.command_issuer.dropTip(0)
