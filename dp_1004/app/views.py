from rest_framework.decorators import api_view
from rest_framework.response import Response
from pymongo import MongoClient
from matplotlib.backends.backend_agg import FigureCanvasAgg
from django.shortcuts import render
from django.http import HttpResponse
import matplotlib.pyplot as plt
import numpy as np
import requests

MONGO_URI = "mongodb+srv://final_project:admin123@cluster0.zlexbip.mongodb.net/"
DATA_API = "https://pokeapi.co/api/v2/pokemon/"

def get_mongo_collection():
    client = MongoClient(MONGO_URI)
    #print(client, "++++++++")
    db = client.dp_1004
    #print(db,"/n *****")
    collection = db["pokemon"]
    return collection

def get_data(pok_num):
    resp = requests.get(DATA_API+str(pok_num))
    if resp.status_code == 200:
        return resp.json()

def create_data_visualizations(pokemon_data):
    # Create subplots with 3 rows and 1 column
    fig, axs = plt.subplots(3, 1, figsize=(8, 18))

    # Bar chart for base_experience and height
    axs[0].bar(['Base Experience', 'Height'], [pokemon_data['base_experience'], pokemon_data['height']], color='skyblue')
    axs[0].set_xlabel('Metrics')
    axs[0].set_ylabel('Values')
    axs[0].set_title('Base Experience and Height of Pokemon')
    axs[0].grid(axis='y', linestyle='--', alpha=0.7)

    # Pie chart for abilities
    labels = pokemon_data['abilities']
    axs[1].pie([1] * len(labels), labels=labels, colors=plt.cm.Paired.colors, startangle=90, autopct='%1.1f%%')
    axs[1].set_title('Distribution of Abilities for Pokemon')
    axs[1].axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Horizontal bar chart for top 10 moves
    move_names = pokemon_data['moves'][:10]
    move_freq = [1] * len(move_names)
    axs[2].barh(move_names, move_freq, color='lightcoral')
    axs[2].set_xlabel('Frequency')
    axs[2].set_ylabel('Move Names')
    axs[2].set_title('Top 10 Moves for Pokemon')

    plt.tight_layout()
    return fig

def fetch_single_data(pokemon_id):
    try:
        collection = get_mongo_collection()
        filter_ = {"pokemon_id": pokemon_id}
        result = collection.find_one(filter_)

        if result:
            # Access specific data from the fetched result
            pokemon_name = result['forms'][0]['name']
            abilities = result['abilities']
            base_experience = result['base_experience']
            height = result['height']

            moves = result.get('moves', [])  # Extract the 'moves' field and provide an empty list if it doesn't exist
            move_names = []

            for move_data in moves:
                move_name = move_data['move']['name']
                move_names.append(move_name)

            # Return the fetched data as a dictionary, including the height and moves
            return {
                'pokemon_name': pokemon_name,
                'abilities': abilities,
                'base_experience': base_experience,
                'height': height,
                'moves': move_names
            }
        else:
            print("No Pokemon found with the given ID.")
            return None

    except Exception as e:
        print(e)
        return None


def fetch_multiple_data(pokemon_ids):
    data_list = []
    for pokemon_id in pokemon_ids:
        data = fetch_single_data(pokemon_id)
        if data:
            data_list.append((data['pokemon_name'], data))  # Append a tuple of (pokemon_name, data)
    return data_list

def get_composite_graph():
    print("&&"*30)
    fig = ""
    pokemon_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    pokemon_data_list = fetch_multiple_data(pokemon_ids)
    if len(pokemon_data_list) == 10:
        attributes = ['abilities', 'base_experience', 'height']
        num_attributes = len(attributes)
        labels = [pokemon_data[0] for pokemon_data in pokemon_data_list]  # Extract Pokemon names from the tuple

        # Normalize data for each attribute to a common scale (between 0 and 1)
        normalized_data = np.zeros((len(pokemon_data_list), num_attributes))
        for i, pokemon_data in enumerate(pokemon_data_list):
            for j, attribute in enumerate(attributes):
                if attribute == 'abilities':
                    # Assign a score of 1 for Pokemon with more abilities
                    normalized_data[i, j] = len(pokemon_data[1][attribute])
                else:
                    # Normalize other numerical attributes to the range [0, 1]
                    max_value = max([data[1][attribute] for data in pokemon_data_list])
                    min_value = min([data[1][attribute] for data in pokemon_data_list])
                    normalized_data[i, j] = (pokemon_data[1][attribute] - min_value) / (max_value - min_value)

        # Create the radar chart
        angles = np.linspace(0, 2 * np.pi, num_attributes, endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))  # Close the loop
        fig, ax = plt.subplots(figsize=(15, 10), subplot_kw=dict(polar=True))
        for i, data in enumerate(normalized_data):
            data = np.concatenate((data, [data[0]]))  # Close the loop
            ax.plot(angles, data, label=labels[i])
            ax.fill(angles, data, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(attributes)
        ax.set_title('Pokemon Power Comparison')
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    else:
        print("Please provide ten Pokemon IDs (ranging from 1 to 10) to compare.")
    return fig

@api_view(['GET', 'POST'])
def get_pokemon_data(request, pk=None):
    try:
        if not pk:
            fig = get_composite_graph()
        else:
            print("^^^"*40)
            data = fetch_single_data(pk)
            fig = create_data_visualizations(data)
        if not fig:
            return HttpResponse("No Vizualisation")
        response = HttpResponse(content_type = 'image/png')
        canvas = FigureCanvasAgg(fig)
        canvas.print_png(response)
        return response
    except Exception as e:
        raise
        return HttpResponse("No Vizualisation")


@api_view(['GET', 'POST'])
def insertdata(request):
    try:
        for pokemon_ in range(1, 6):
#            print(pokemon_, "%%%" * 10)
            data = get_data(pokemon_)
            if data:
                collection = get_mongo_collection()
                # Define a filter to check if the data already exists in the collection
                filter_ = {"pokemon_id": data["id"]}  # Assuming "pokemon_id" is the unique identifier for each record
                print(filter_, "################################")
                if filter_["pokemon_id"] is int:
                    collection.insert_one(data)
                else:
                    print("id exists")
        return Response({"message": "Inserted Data"})
    except Exception as e:
        print(e)

#In this modified code, the filter_ variable is used to check if a record with the same pokemon_id already exists in the collection. If it does, the update_one() method will update the existing record with the new data. If it does not exist, the upsert=True parameter will cause update_one() to insert a new record with the provided data.


@api_view(['GET', 'POST'])
def showdata(request):
    return render(request, 'app/index.html', context={'file_name': 'abcd.jpg'})

# {{context.file_name}}



