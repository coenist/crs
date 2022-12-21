#imports
import crs
from shapely.geometry import Point
import sys
import pandas as pd

def main():
    args = sys.argv[1:]
    if len(args) == 0:
        print('No parameters provided. Please provide the following parameters:')
        print('\t-x: X-coordinate of the position (required)')
        print('\t-y: Y-coordinate of the position (required)')
        print('\t-q: Locality of the position  (required)')
        print('\t-b: Buffer  (optional)')
    else:
        if '-x' not in args:
            print('X-coordinate missing. Use "-x" argument to add')
        elif '-y' not in args:
            print('Y-coordinate missing. Use "-y" argument to add')
        elif '-q' not in args:
            print('Locality missing. Use "-q" argument to add')
        else:
            givenX = float(args[args.index('-x') + 1])
            givenY = float(args[args.index('-y') + 1])
            locality = args[args.index('-q') + 1]
            if '-b' not in args:
                print('No buffer distance provided. A buffer of 15 km will be used as default value')
                buffer = 15000
            else:
                buffer = float(args[args.index('-b') + 1])
            refList = crs.geocode(locality)
            givenPoint = Point(givenX, givenY)
            threshold = sys.maxsize
            
            refPointIter = iter(refList)
            bestCRSdf = pd.DataFrame({"dist": threshold}, index=[0])
            while (refPoint := next(refPointIter, None)) is not None and threshold > buffer:
                candidates = crs.getCandidateList(refPoint, buffer)
                assessmentDf = crs.evaluateCRSList(candidates, givenPoint, refPoint)
                threshold = assessmentDf.iloc[0]['dist']
                if threshold < bestCRSdf.iloc[0]['dist']:
                    bestCRSdf = assessmentDf
                    threshold = assessmentDf.iloc[0]['dist']
                
            bestCRSdf['dist'] = bestCRSdf['dist'] / 1000
            print(bestCRSdf.head(10))

if __name__ == "__main__":
    main()
