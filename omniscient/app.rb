require 'sinatra'
require 'yaml'
require 'json'
require 'yahoo_weatherman'
require 'google_directions'
require 'wolfram-alpha'
require 'imdb'

configure do
  set :conf, YAML.load_file("config.yml") rescue nil || {}
end

helpers do
  def json_status(code, reason)
    status code
    {
      :status => code,
      :reason => reason
    }.to_json
  end
  def accept_params(params, *fields)
    h = { }
    fields.each do |name|
      h[name] = params[name] if params[name]
    end
    h
  end
  # TODO
  def movie_details(id)
    i = Imdb::Movie.new(id)
    deets = {}
    deets['title'] = i.title
    deets['cast'] = i.cast_members.take(5)
    deets['director'] = i.director
    deets['year'] = i.year
    deets['rating'] = i.rating
    deets.to_json
  end
end

get "/" do
  "Welcome to Ernie!"
end

get "/weather/:location" do
  return json_status 400, "Missing param" unless params[:location]
  content_type :json
  location = params[:location]
  weather = {}
  # hsh.each_pair{ |k,v| puts "#{k}: #{v}"}
  client = Weatherman::Client.new
  response = client.lookup_by_location("#{location}")
  if response.description.include? "Invalid Input"
    return json_status 404, "Not found"
  end
  weather['temp'] = response.condition['temp'] || ''
  weather['desc'] = response.condition['text'] || ''
  forecast = response.forecasts[2]
  weather['forecast'] = forecast['text'] || ''
  weather.to_json
  #http://ruby-doc.org/gems/docs/y/yahoo_weatherman-2.0.0/Weatherman/Response.html#method-i-forecasts
end

get "/goto/:origin/:destination" do
  return json_status 400, "Missing param" unless params[:destination]
  content_type :json
  origin = params[:origin]
  destination = params[:destination]
  # If params origin is missing, just give back the "address"
  directions = GoogleDirections.new(origin, destination)
  result = directions.xml.to_json
  puts result.inspect
end

get "/movie/:title" do
  return json_status 400, "Missing param" unless params[:title]
  content_type :json
  title = params[:title]
  response = Imdb::Search.new("#{title}")
  if response.movies.size > 0
    movie = response.movies.first
    return movie_details(movie.id)
  end
end

# TODO
get "/any/:whatever" do
  return json_status 500, "Missing config" if settings.conf['api']['wolfram_key'].nil?
  content_type :json
  whatever = params[:whatever]

  options = { "format" => "plaintext" } # see the reference appendix in the documentation.[1]

  client = WolframAlpha::Client.new settings.conf['api']['wolfram_key'], options

  response = client.query "#{whatever}"
  input = response["Input"] # Get the input interpretation pod.
  query_result = response.queryresult
  return json_status 500, "API failed" if queryresult.success == 'false'
  return json_status 400, "Not found" if queryresult.error == 'true'

  result = response.find { |pod| pod.title == 'Result' } # Get the result pod.
  if result.nil?
    result = response.find { |pod| pod.title == 'Basic information' }
  end
  "#{input.subpods[0].plaintext} = #{result.subpods[0].plaintext}"
end
