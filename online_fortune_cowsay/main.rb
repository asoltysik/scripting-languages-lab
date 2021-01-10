require 'sinatra'
require "sinatra/reloader"
require "rubygems"
require "rom"
require "rom-repository"

Tilt.register Tilt::ERBTemplate, 'html.erb'

rom = ROM.container(:sql, 'sqlite::memory') do |conf|
  conf.default.connection.create_table(:history) do
    primary_key :id
    column :when, DateTime, null: false
    column :text, String, null: false
    column :ip, String, null:false
  end

  conf.relation(:history) do
    schema(infer: true)
  end
end

class HistoryRepo < ROM::Repository[:history]
  commands :create

  def get_all
    history.order{}.to_a.sort_by(&:when).reverse
  end
end

history_repo = HistoryRepo.new(rom)

get '/' do
  quote = random_quote
  str_in_block = blockify quote

  history_repo.create(when: DateTime.now, text: quote, ip: request.ip)

  whole_history = history_repo.get_all

  erb :main, :locals => { :quote => str_in_block, :history => whole_history }
end

def blockify(str)
  lines = str.gsub("\t", " ").split(/\n/)
  total_lines = lines.length

  max_len = lines.map { |line| line.length }.max

  if max_len == 0
    return ""
  end

  "_" * (max_len + 2) +
    "\n" +
    lines.each_with_index.map { |line, i|
      start(i, total_lines) + line + (" " * (max_len - line.length)) + finish(i, total_lines)
    }.join("\n") +
    "\n " +
    "-" * (max_len + 2) + "\n"
end

def start(i, total)
  if i == 0
    "/ "
  elsif i == total - 1
    "\\ "
  else
    "| "
  end
end

def finish(i, total)
  if i == 0
    " \\"
  elsif i == total - 1
    " /"
  else
    " |"
  end
end

def random_quote
  file = File.open('riddles', 'r')
  data = file.read

  split = data.split(/%/)
  split.sample
end