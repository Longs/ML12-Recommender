import pdb
import numpy as np
import time
import pickle

genres = ['Western', 'Comedy', 'Children', 'Crime', 'Musical',
          'Adventure', 'Drama', 'Horror', 'War', 'Documentary',
          'Romance', 'Animation', 'Film-Noir', 'Sci-Fi', 'Mystery',
          'Fantasy', 'IMAX', 'Action', 'Thriller']

# Data is a list of (a, i, r) triples
ratings_small = \
[(0, 0, 5), (0, 1, 3), (0, 3, 1),
 (1, 0, 4), (1, 3, 1),
 (2, 0, 1), (2, 1, 1), (2, 3, 5),
 (3, 0, 1), (3, 3, 4),
 (4, 1, 1), (4, 2, 5), (4, 3, 4)]

def pred(data, x):
    (a, i, r) = data
    (u, b_u, v, b_v) = x
    return np.dot(u[a].T,v[i]) + b_u[a] + b_v[i]

# X : n x k
# Y : n
def ridge_analytic(X, Y, lam):
    (n, k) = X.shape
    xm = np.mean(X, axis = 0, keepdims = True)   # 1 x n
    ym = np.mean(Y)                              # 1 x 1
    Z = X - xm                                   # d x n
    T = Y - ym                                   # 1 x n
    th = np.linalg.solve(np.dot(Z.T, Z) + lam * np.identity(k), np.dot(Z.T, T))
    # th_0 account for the centering
    th_0 = (ym - np.dot(xm, th))                 # 1 x 1
    return th.reshape((k,1)), float(th_0)

# Example from lab handout
Z = np.array([[1], [1], [5], [1], [5], [5], [1]])
b_v = np.array([[3], [3], [3], [3], [3], [5], [1]])
B = np.array([[1, 10], [1, 10], [10, 1], [1, 10], [10, 1], [5, 5], [5, 5]])
# Solution with offsets, using ridge_analytic provided in code file
u_a, b_u_a = ridge_analytic(B, (Z - b_v), 1)
print('With offsets', u_a, b_u_a)

new_llama = np.array([[10],[1]])
#print(f"new llama with offsets {np.dot(u_a,new_llama) + b_u_a + 1}")
print(f"new llama with offsets {np.dot(np.transpose(u_a),new_llama) + b_u_a + 1}")



# Solution using previous model, with no offsets
u_a_no_b = np.dot(np.linalg.inv(np.dot(B.T, B) + 1 * np.identity(2)), np.dot(B.T, Z))
print('With no offsets', u_a_no_b)
print(f"new llama WITHOUT offsets {np.dot(np.transpose(u_a_no_b),new_llama)}")

new_robot = np.array([[1],[10]])

print(f"new robot WITHOUT offsets {np.dot(np.transpose(u_a_no_b),new_robot)}")

print(f"new robot with offsets {np.dot(np.transpose(u_a),new_robot) + b_u_a + 5}")

# After retrieving the output x from mf_als, you can use this function to save the output so
# you don't have to re-train your model
def save_model(x):
    pickle.dump(x, open("ALSmodel", "wb"))

# After training and saving your model once, you can use this function to retrieve the previous model
def load_model():
    x = pickle.load(open("ALSmodel", "rb"))
    return x

# Compute the root mean square error
def rmse(data, x):
    error = 0.
    for datum in data:
        error += (datum[-1] - pred(datum, x))**2
    return np.sqrt(error/len(data))

# Counts of users and movies, used to calibrate lambda
def counts(data, index):
    item_count = {}
    for datum in data:
        j = datum[index]
        if j in item_count:
            item_count[j] += 1
        else:
            item_count[j] = 1
    c = np.ones(max(item_count.keys())+1)
    for i,v in item_count.items(): c[i]=v
    return c

# The ALS outer loop
def mf_als(data_train, data_validate, k=2, lam=0.02, max_iter=100, verbose=False):
    # size of the problem
    n = max(d[0] for d in data_train)+1 # users
    m = max(d[1] for d in data_train)+1 # items
    # which entries are set in each row and column
    us_from_v = [[] for i in range(m)]
    vs_from_u = [[] for a in range(n)]
    for (a, i, r) in data_train:
        us_from_v[i].append((a, r))
        vs_from_u[a].append((i, r))
    # Initial guess at u, b_u, v, b_v
    # Note that u and v are lists of column vectors (columns of U, V).
    x = ([np.random.normal(1/k, size=(k,1)) for a in range(n)],
          np.zeros(n),
          [np.random.normal(1/k, size=(k,1)) for i in range(m)],
          np.zeros(m))
    # Alternation, modifies the contents of x
    start_time = time.time()
    for i in range(max_iter):
        update_U(data_train, vs_from_u, x, k, lam)
        update_V(data_train, us_from_v, x, k, lam)
        if verbose:
            print('train rmse', rmse(data_train, x), 'validate rmse', data_validate and rmse(data_validate, x))
        if data_validate == None: # code is slower, print out progress
            print("Iteration {} finished. Total Elapsed Time: {:.2f}".format(i + 1, time.time() - start_time))
    # The root mean square errors measured on validate set
    if data_validate != None:
        print('ALS result for k =', k, ': rmse train =', rmse(data_train, x), '; rmse validate =', rmse(data_validate, x))
    return x

""" def update_U(data, vs_from_u, x, k, lam):
    (u, b_u, v, b_v) = x

    for _,user in enumerate(vs_from_u):
        user_X=[]
        user_Y=[]
        for index,rating in user:
            user_X.append(np.transpose(v[index])[0])
            user_Y.append([rating - b_v[index][0]]) #TODO: correct or b_v - so rating - b_v
        
        #do not update if no ratings
        if np.max(user_Y) > 0:
            X=np.array(user_X)
            Y=np.array(user_Y)
            u[_], b_u[_] = ridge_analytic(X, Y, lam)

    x = (u, b_u, v, b_v)
    return x """

def update_U(data, vs_from_u, x, k, lam):
    (u, b_u, v, b_v) = x
    for a in range(len(u)):
        if not vs_from_u[a]: continue
        V = np.hstack([v[i] for (i, _) in vs_from_u[a]]).T
        y = np.array([r-b_v[i] for (i, r) in vs_from_u[a]])
        u[a], b_u[a] = ridge_analytic(V, y, lam)
    return x

#Test case for update_U
def update_U_test():
  '''
  This is a test function provided to help you debug your implementation
  '''
  k = 2
  lam = 0.01
  
  vs_from_u = \
  [[(0, 5), (1, 3), (3, 1)],
   [(0, 4), (3, 1)],
   [(0, 1), (1, 1), (3, 5)],
   [(0, 1), (3, 4)],
   [(1, 1), (2, 5), (3, 4)]]
  
  np.random.seed(0)
  
  first = []
  for i in range(5):
    first.append(np.random.rand(2, 1))
  second = np.zeros((5, 1))
  third = []
  for i in range(5):
    third.append(np.random.rand(2, 1))
  fourth = np.zeros((5, 1))
  x0 = (first, second, third, fourth)
  
  x_result = update_U(ratings_small, vs_from_u, x0, k, lam)
  
  x_list = [[u.tolist() for u in x_result[0]],
            x_result[1].tolist(),
            [v.tolist() for v in x_result[2]],
            x_result[3].tolist()]
  
  
  assert np.all(np.isclose(x_list[0], np.array([[[4.048442188078757], [-2.5000082235465526]],
                                                [[3.2715388359271054], [-1.2879317400952521]],
                                                [[-6.237522315961142], [-2.9639103597721355]],
                                                [[-3.2715388359271054], [1.2879317400952521]],
                                                [[-4.87111151185168], [-1.761023196019822]] ])))
  assert np.all(np.isclose(x_list[1], 
                           np.array([[3.043665230868208], [2.048616799474877], [7.462166369240114], [2.951383200525123], [5.487071919883842]])))
  assert np.all(np.isclose(x_list[2], np.array([[[0.7917250380826646], [0.5288949197529045]],
                                       [[0.5680445610939323], [0.925596638292661]],
                                       [[0.07103605819788694], [0.08712929970154071]],
                                       [[0.02021839744032572], [0.832619845547938]],
                                       [[0.7781567509498505], [0.8700121482468192]] ])))
  assert np.all(np.isclose(x_list[3], np.array([[0.0], [0.0], [0.0], [0.0], [0.0]])))
  print("Test passed!")
  
update_U_test()


def update_V(data, us_from_v, x, k, lam):
    (u, b_u, v, b_v) = x
    for i in range(len(v)):
        if not us_from_v[i]: continue
        V = np.hstack([u[a] for (a, _) in us_from_v[i]]).T
        y = np.array([r-b_u[a] for (a, r) in us_from_v[i]])
        v[i], b_v[i] = ridge_analytic(V, y, lam)
    return x

# Simple validate case
mf_als(ratings_small, ratings_small,lam=0.01, max_iter=10, k=2)

# The SGD outer loop
def mf_sgd(data_train, data_validate, step_size_fn, k=2, lam=0.02, max_iter=100, verbose=False):
    # size of the problem
    ndata = len(data_train)
    n = max(d[0] for d in data_train)+1
    m = max(d[1] for d in data_train)+1
    # Distribute the lambda among the users and items
    lam_uv = lam/counts(data_train,0), lam/counts(data_train,1)
    # Initial guess at u, b_u, v, b_v (also b)
    x = ([np.random.normal(1/k, size=(k,1)) for j in range(n)],
         np.zeros(n),
         [np.random.normal(1/k, size=(k,1)) for j in range(m)],
         np.zeros(m))
    di = int(max_iter/10.)
    for i in range(max_iter):
        if i%di == 0 and verbose:
            print('i=', i, 'train rmse=', rmse(data_train, x),
                  'validate rmse', data_validate and rmse(data_validate, x))
        step = step_size_fn(i)
        j = np.random.randint(ndata)            # pick data item
        sgd_step(data_train[j], x, lam_uv, step) # modify x
    print('SGD result for k =', k, ': rmse train =', rmse(data_train, x), '; rmse validate =', rmse(data_validate, x))
    return x

def sgd_step(data, x, lam, step):
    (a, i, r) = data
    (u, b_u, v, b_v) = x
    (lam_u, lam_v) = lam
    # predicted rating
    pred = np.dot(u[a].T,v[i]) + b_u[a] + b_v[i]
    # prediction error
    e = r - pred
    temp_u = u[a]           # so we don't update v with updated u
    u[a] = u[a] - step*(-e*v[i] + lam_u[a]*u[a])
    b_u[a] = b_u[a] - step*(-e)
    v[i] = v[i] - step*(-e*temp_u + lam_v[i]*v[i])
    b_v[i] = b_v[i] - step*(-e)
    return x

def sgd_step_test():
  '''
  This is a test function provided to help you debug your implementation
  '''
  step = 0.025
  lam =(np.array([ 0.00333333,  0.005,  0.00333333,  0.005,  0.00333333]), np.array([ 0.0025,  0.00333333,  0.01,  0.002]))
  
  np.random.seed(0)
  
  first = []
  for i in range(5):
    first.append(np.random.rand(2, 1))
  second = np.zeros((5, 1))
  third = []
  for i in range(5):
    third.append(np.random.rand(2, 1))
  fourth = np.zeros((5, 1))
  x0 = (first, second, third, fourth)
  
  x_result = sgd_step(ratings_small[3], x0, lam, step)
  
  x_list = [[u.tolist() for u in x_result[0]],
            x_result[1].tolist(),
            [v.tolist() for v in x_result[2]],
            x_result[3].tolist()]
    
  assert np.all(np.isclose(x_list[0], np.array([[[0.5488135039273248], [0.7151893663724195]],
                                                [[0.6667107015911342], [0.5875840438721468]],
                                                [[0.4236547993389047], [0.6458941130666561]],
                                                [[0.4375872112626925], [0.8917730007820798]],
                                                [[0.9636627605010293], [0.3834415188257777]]])))
  assert np.all(np.isclose(x_list[1], np.array([[0.0], [0.08086477989447478], [0.0], [0.0], [0.0]])))
  assert np.all(np.isclose(x_list[2], np.array([[[0.8404178830022684], [0.5729237224816648]],
                                                [[0.5680445610939323], [0.925596638292661]],
                                                [[0.07103605819788694], [0.08712929970154071]],
                                                [[0.02021839744032572], [0.832619845547938]],
                                                [[0.7781567509498505], [0.8700121482468192]]])))
  assert np.all(np.isclose(x_list[3], np.array([[0.08086477989447478], [0.0], [0.0], [0.0], [0.0]])))
  print("Test passed!")
  
sgd_step_test()


# Simple validate case
mf_sgd(ratings_small, ratings_small, step_size_fn=lambda i: 0.1,
       lam=0.01, max_iter=1000, k=2)

def load_ratings_data_small(path_data='ratings.csv'):
    """
    Returns two lists of triples (a, i, r) (training, validate)
    """
    # we want to "randomly" sample but make it deterministic
    def user_hash(uid):
        return 71 * uid % 401
    def user_movie_hash(uid, iid):
        return (17 * uid + 43 * iid) % 61
    data_train = []
    data_validate = []
    with open(path_data) as f_data:
        for line in f_data:
            (uid, iid, rating, timestamp) = line.strip().split(",")
            h1 = user_hash(int(uid))
            if h1 <= 40:
                h2 = user_movie_hash(int(uid), int(iid))
                if h2 <= 12:
                    data_validate.append([int(uid), int(iid), float(rating)])
                else:
                    data_train.append([int(uid), int(iid), float(rating)])
    print('Loading from', path_data,
          'users_train', len(set(x[0] for x in data_train)),
          'items_train', len(set(x[1] for x in data_train)),
          'users_validate', len(set(x[0] for x in data_validate)),
          'items_validate', len(set(x[1] for x in data_validate)))
    return data_train, data_validate

def load_ratings_data(path_data='ratings.csv'):
    """
    Returns a list of triples (a, i, r)
    """
    data = []
    with open(path_data) as f_data:
        for line in f_data:
            (uid, iid, rating, timestamp) = line.strip().split(",")
            data.append([int(uid), int(iid), float(rating)])

    print('Loading from', path_data,
          'users', len(set(x[0] for x in data)),
          'items', len(set(x[1] for x in data)))
    return data

def load_movies(path_movies='movies.csv'):
    """
    Returns a dictionary mapping item_id to item_name and another dictionary
    mapping item_id to a list of genres
    """
    data = {}
    genreMap = {}
    with open(path_movies, encoding = "utf8") as f_data:
        for line in f_data:
            parts = line.strip().split(",")
            item_id = int(parts[0])
            item_name = ",".join(parts[1:-1]) # file is poorly formatted
            item_genres = parts[-1].split("|")
            data[item_id] = item_name
            genreMap[item_id] = item_genres
    return data, genreMap

def baseline(train, validate):
    item_sum = {}
    item_count = {}
    total = 0
    for (i, j, r) in train:
        total += r
        if j in item_sum:
            item_sum[j] += 3
            item_count[j] += 1
        else:
            item_sum[j] = r
            item_count[j] = 1
    error = 0
    avg = total/len(train)
    for (i, j, r) in validate:
        pred = item_sum[j]/item_count[j] if j in item_count else avg
        error += (r - pred)**2
    return np.sqrt(error/len(validate))

# Load the movie data
# Below is code for the smaller dataset, used in section 3 of the HW
def tuning_als(max_iter_als=20, verbose=False):
    b1, v1 = load_ratings_data_small()
    print('Baseline rmse (predict item average)', baseline(b1, v1))
    print('Running on the MovieLens data')
    lams = [0.1,1,10,100]
    ks = [1,2,3]
    for k in ks:
        for lam in lams:
            print('ALS, k =', k, 'and lam', lam)
            mf_als(b1, v1, lam = lam, max_iter=max_iter_als, k=k, verbose=verbose)

#data = load_ratings_data()
data = load_ratings_data()
movies_dict, genres_dict = load_movies()
#model = mf_als(data, None, k=10, lam=1, max_iter=20)
#save_model(model)

model = load_model()

#should do this in pandas but MIT don't understand it
user_data=[]

sum_genres ={}
for genre in genres:
    sum_genres[genre]=0

#gen=((a,i,r) for a,i,r in data if a==270894 and r==5)

USER_OF_INTEREST=270894
films_watched = []

for a,i,r in ((a,i,r) for a,i,r in data if a==USER_OF_INTEREST):
    films_watched.append(i)
    if (r == 5):
        for genre in (genres_dict[i]):
            sum_genres[genre]+=1

most_watched = genres[np.argmax(list(sum_genres.values()))]

print(f"most popular for this user is {most_watched}")

u,b_u,v,b_v = model
#u = model[0][USER_OF_INTEREST]
#b_u = model[1][USER_OF_INTEREST]
prediction = {}
v_dict={}
b_v_dict={}

for movie_index,film_v in enumerate(v):
    v_dict[movie_index] = film_v

for movie_index,film_b_v in enumerate(b_v):
    b_v_dict[movie_index] = film_b_v

for movie_index in movies_dict.keys():
    #b_v = model[3][movie_index]
    if not movie_index in films_watched:
        #prediction.append((np.dot(np.transpose(u[USER_OF_INTEREST]),v_dict[movie_index]) + b_u[USER_OF_INTEREST] + b_v_dict[movie_index])[0][0])
        prediction[movie_index]=(u[USER_OF_INTEREST].T.dot(v[movie_index])+b_u[USER_OF_INTEREST]+ b_v[movie_index])[0][0]

""" #Their code

movies_seen = set(i for a, i, _ in data if a == 270894)
preds = {}
for i in movies_dict:
    if i in movies_seen: continue
    preds[i] = u[270894].T.dot(v[i])+b_u[270894]+b_v[i]
num_animation = 0
for i in sorted(preds, key=lambda k: preds[k])[-50:]:
    print(f"{movies_dict[i]}: {genres_dict[i]}: {preds[i]}")
    if "Animation" in genres_dict[i]:
        num_animation += 1
print("Number matching favorite genre:", num_animation)
 """



top_50 = sorted(prediction, key = lambda k: prediction[k])[-50:]
top = 0
for _ in top_50:
    print(f"{movies_dict[_]}: {genres_dict[_]}{prediction[_]}")
    if most_watched in genres_dict[_]:
        top += 1

def similarity(v_a,v_b):
    def mag(x):
        return (np.dot(x.T,x))**0.5
    return np.dot(np.transpose(v_a),v_b)/(mag(v_a)*mag(v_b))



def most_similar_to(to):
    sim={}
    for movie_index in movies_dict.keys():
        sim[movie_index] = similarity(v[to],v[movie_index])
    sim.pop(to)

    most_sim = sorted(sim,key=lambda k: sim[k])[-10:]
    return most_sim

out = most_similar_to(260)
print(out)
for _,movie in enumerate(out):
    print(f"{movie}: {movies_dict[movie]}: {genres_dict[movie]}: {similarity(v[260],v[movie])}")

out = most_similar_to(2628)
print(out)
for _,movie in enumerate(out):
    print(f"{movie}: {movies_dict[movie]}: {genres_dict[movie]}: {similarity(v[2628],v[movie])}")


print(f"Number of movies outside favourite genre: {top}")


#4.2.d average similarity - works fine
similarities=[]
com_sim={}
gen_sim={} #similarity within a genre
for g in genres:
    gen_sim[g]=[]
    com_sim[g]=[]

movies = list(movies_dict.keys())
for _,movie_1 in enumerate(movies):
    for movie_2 in movies[_+1:]:
        s = similarity(v[movie_1],v[movie_2])
        similarities.append(s)
        if 'Comedy' in genres_dict[movie_1]:
            for g in genres_dict[movie_2]:
                com_sim[g].append(s)

        for g in genres_dict[movie_1]:
            if g in genres_dict[movie_2]:
                gen_sim[g].append(s)

print (f"average similarity: {np.average(similarities)}")
for g in genres:
    print(f"genre {g} average similarity{np.average(gen_sim[g])}")

#4.2E) similarity within genre
for g in genres:
    print(f"genre {g} average similarityto Comedy {np.average(com_sim[g])}")









"""
for genres_list in top_genres:
    for genre in genres_list:
        sum_genres[genre] +=1

 """

""" genre_count={}
for genre in genres:
    genre_count[genre]=np.char.count(top_genres,genre)
    print(genre, "" ,genre_count[genre])


import pandas as pd

pd_movies = pd.read_csv("movies.csv",header=None,names=["index","name","genre"])
pd_ratings = pd.read_csv("ratings.csv",header=None, names=["a","i","r"],index_col=False)

pd_movies.info()
pd_ratings.info()

user_ratings = pd_ratings[pd_ratings["a"]==270894]
user_ratings.info()
print("t")

"""