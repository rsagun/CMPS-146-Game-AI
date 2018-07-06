from random import choice, random

#plant density and prey density are calculated based on other traits in init()
all_traits = {
    'temperature': random(),
    'plant density': random(),
    'prey density': random(),
    'humidity': random(),
    'elevation': random(),
    'geovariance': random(),
    'fertility': random(),
    'sun exposure': random(),
    'precipitation': random(),
    'wind': random(),
    'barometric pressure': random(),
    'natural disaster': random(),
    'pollution': random(),
    'hostility': random()
}

class Environment:
    def __init__(self, traits={}):
        self.traits = traits if traits else {key: value for key, value in all_traits.items()}

        pd = self.traits['temperature'] * .05 \
             + self.traits['elevation'] * .05 \
             + self.traits['sun exposure'] * .1 \
             + self.traits['humidity'] * .4 \
             + self.traits['fertility'] * .4

        ad = pd - self.traits['elevation'] * .1 - self.traits['geovariance'] * .1

        self.traits['plant density'] = pd
        self.traits['prey density'] = ad

    def __repr__(self):
        return '\n'.join([str(key) + ": " + str('%.2f' % value) for key, value in self.traits.items()])


def main():
    jungle = Environment({'temperature': .6, 'humidity': .9, 'elevation': .4, 'geovariance': .5, 'fertility': .8, 'sun exposure': .5})
    desert = Environment({'temperature': 1, 'humidity': 0, 'elevation': 0, 'geovariance': .1, 'fertility': 0, 'sun exposure': 1})
    print(str(jungle) + '\n')
    print(desert)


if __name__ == '__main__':
    main()
