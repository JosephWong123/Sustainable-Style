from google.cloud import vision, storage
import os
import cloudstorage as gcs

from main import CLOUD_STORAGE_BUCKET

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key/creds.json"

def create_product_set(
        project_id, location, product_set_id, product_set_display_name):
    """Create a product set.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_set_id: Id of the product set.
        product_set_display_name: Display name of the product set.
    """
    client = vision.ProductSearchClient()

    # A resource that represents Google Cloud Platform location.
    location_path = client.location_path(
        project=project_id, location=location)

    # Create a product set with the product set specification in the region.
    product_set = vision.types.ProductSet(
            display_name=product_set_display_name)

    # The response is the product set with `name` populated.
    response = client.create_product_set(
        parent=location_path,
        product_set=product_set,
        product_set_id=product_set_id)

    # Display the product set information.
    print('Product set name: {}'.format(response.name))

def import_product_sets(project_id, location, gcs_uri):
    """Import images of different products in the product set.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        gcs_uri: Google Cloud Storage URI.
            Target files must be in Product Search CSV format.
    """
    client = vision.ProductSearchClient()

    # A resource that represents Google Cloud Platform location.
    location_path = client.location_path(
        project=project_id, location=location)

    # Set the input configuration along with Google Cloud Storage URI
    gcs_source = vision.types.ImportProductSetsGcsSource(
        csv_file_uri=gcs_uri)
    input_config = vision.types.ImportProductSetsInputConfig(
        gcs_source=gcs_source)

    # Import the product sets from the input URI.
    response = client.import_product_sets(
        parent=location_path, input_config=input_config)

    print('Processing operation name: {}'.format(response.operation.name))
    # synchronous check of operation status
    result = response.result()
    print('Processing done.')

    print(result.statuses)
    for i, status in enumerate(result.statuses):
        print('Status of processing line {} of the csv: {}'.format(
            i, status))
        # Check the status of reference image
        # `0` is the code for OK in google.rpc.Code.
        if status.code == 0:
            reference_image = result.reference_images[i]
            print(reference_image)
        else:
            print('Status code not OK: {}'.format(status.message))

def delete_product_set(project_id, location, product_set_id):
    """Delete a product set.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_set_id: Id of the product set.
    """
    client = vision.ProductSearchClient()

    # Get the full path of the product set.
    product_set_path = client.product_set_path(
        project=project_id, location=location,
        product_set=product_set_id)

    # Delete the product set.
    client.delete_product_set(name=product_set_path)
    print('Product set deleted.')

def get_similar_products_file(
        project_id, location, product_set_id, product_category,
        file_path, filter):
    """Search similar products to image.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_set_id: Id of the product set.
        product_category: Category of the product.
        file_path: Local file path of the image to be searched.
        filter: Condition to be applied on the labels.
        Example for filter: (color = red OR color = blue) AND style = kids
        It will search on all products with the following labels:
        color:red AND style:kids
        color:blue AND style:kids
    """
    # product_search_client is needed only for its helper methods.
    product_search_client = vision.ProductSearchClient()
    image_annotator_client = vision.ImageAnnotatorClient()

    # Read the image as a stream of bytes.
    with open(file_path, 'rb') as image_file:
        content = image_file.read()

    # Create annotate image request along with product search feature.
    image = vision.types.Image(content=content)

    # product search specific parameters
    product_set_path = product_search_client.product_set_path(
        project=project_id, location=location,
        product_set=product_set_id)
    product_search_params = vision.types.ProductSearchParams(
        product_set=product_set_path,
        product_categories=[product_category],
        filter=filter)
    image_context = vision.types.ImageContext(
        product_search_params=product_search_params)

    # Search products similar to the image.
    response = image_annotator_client.product_search(
        image, image_context=image_context)

    results = response.product_search_results.results
    return results
    # print('Search results:')
    # for result in results:
    #     product = result.product
    #
    #     print('Score(Confidence): {}'.format(result.score))
    #     print('Image name: {}'.format(result.image))
    #
    #     print('Product name: {}'.format(product.name))
    #     print('Product display name: {}'.format(
    #         product.display_name))
    #     print('Product description: {}\n'.format(product.description))
    #     print('Product labels: {}\n'.format(product.product_labels))


def delete_all_sets(project_id, location):
    client = vision.ProductSearchClient()

    # A resource that represents Google Cloud Platform location.
    location_path = client.location_path(
        project=project_id, location=location)

    # List all the product sets available in the region.
    product_sets = client.list_product_sets(parent=location_path)

    for product_set in product_sets:
        delete_product_set(project_id, location, product_set.name.split('/')[-1])

def get_similar_products_remote(
        project_id, location, product_set_id, product_category,
        blob_name, filter):
    """Search similar products to image.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_set_id: Id of the product set.
        product_category: Category of the product.
        uri: GCS uri to file
        filter: Condition to be applied on the labels.
        Example for filter: (color = red OR color = blue) AND style = kids
        It will search on all products with the following labels:
        color:red AND style:kids
        color:blue AND style:kids
    """
    # product_search_client is needed only for its helper methods.
    product_search_client = vision.ProductSearchClient()
    image_annotator_client = vision.ImageAnnotatorClient()

    DESTINATION = 'downloaded_file.png'
    # Read the image as a stream of bytes.
    storage_client = storage.Client()
    bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(DESTINATION)

    with open(DESTINATION, 'rb') as image_file:
        content = image_file.read()

    # Create annotate image request along with product search feature.
    image = vision.types.Image(content=content)

    # product search specific parameters
    product_set_path = product_search_client.product_set_path(
        project=project_id, location=location,
        product_set=product_set_id)
    product_search_params = vision.types.ProductSearchParams(
        product_set=product_set_path,
        product_categories=[product_category],
        filter=filter)
    image_context = vision.types.ImageContext(
        product_search_params=product_search_params)

    # Search products similar to the image.
    response = image_annotator_client.product_search(
        image, image_context=image_context)

    results = response.product_search_results.results

    return results
    # for result in results:
    #     product = result.product
    #
    #     print('Score(Confidence): {}'.format(result.score))
    #     print('Image name: {}'.format(result.image))
    #
    #     print('Product name: {}'.format(product.name))
    #     print('Product display name: {}'.format(
    #         product.display_name))
    #     print('Product description: {}\n'.format(product.description))
    #     print('Product labels: {}\n'.format(product.product_labels))

if __name__ == '__main__':
    pass
    # get_similar_products_file('hack-sc-2020', 'us-west1', "product-list", "apparel-v2", "TestFiles/hmgoepprod.jpeg", "")
