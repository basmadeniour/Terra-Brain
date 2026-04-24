import tkinter as tk
from tkinter import ttk
import folium
from folium import plugins
import tempfile
import os
import sys
import json
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget
from PyQt5.QtCore import QUrl, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

from .colors import MapColors


class MapBridge(QObject):
    location_selected = pyqtSignal(float, float)
    polygon_drawn = pyqtSignal(list)

    @pyqtSlot()
    def ready(self):
        print("Bridge ready")

    @pyqtSlot(float, float)
    def select_location(self, lat, lon):
        self.location_selected.emit(lat, lon)

    @pyqtSlot(list)
    def receive_polygon(self, coords):
        self.polygon_drawn.emit(coords)


class MapView:
    
    def __init__(self, parent, city_graph):
        self.parent = parent
        self.graph = city_graph
        self.map = None
        self.temp_file = None
        self.qt_app = None
        self.qt_widget = None
        self.qt_container = None
        self.web_view = None
        self.map_initialized = False
        self.current_center_lat = 31.0364
        self.current_center_lon = 31.3807
        
        self.wide_locations = []
        self.fine_locations = []
        
        self._bridge = MapBridge()
        self.setup_map()
        self.parent.after(500, self.init_map)
    
    @property
    def bridge(self):
        return self._bridge
    
    def setup_map(self):
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        center_container = ttk.Frame(control_frame)
        center_container.pack(expand=True)
        
        ttk.Button(center_container, text="Show Map", command=self.show_map).pack(side=tk.LEFT, padx=2)
        ttk.Button(center_container, text="Show Locations", command=self.show_locations).pack(side=tk.LEFT, padx=2)
        ttk.Button(center_container, text="Show Trees", command=self.show_trees).pack(side=tk.LEFT, padx=2)
        ttk.Button(center_container, text="Pollution Heatmap", command=self.show_heatmap).pack(side=tk.LEFT, padx=2)
        
        self.map_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        self.map_frame.pack(fill=tk.BOTH, expand=True)
        
        self.placeholder = ttk.Label(self.map_frame, text="Loading map...", font=('Arial', 12))
        self.placeholder.pack(expand=True)
    
    def store_locations_data(self, wide_locations, fine_locations):
        self.wide_locations = wide_locations
        self.fine_locations = fine_locations
    
    def show_all_locations(self):
        if not self.map_initialized:
            self.parent.after(1000, self.show_all_locations)
            return
        
        locations_data = []
        if self.wide_locations or self.fine_locations:
            for loc in self.wide_locations + self.fine_locations:
                if isinstance(loc, dict) and 'location' in loc:
                    lat, lon = loc['location']
                    land_type = loc.get('land_type', 'empty')
                    has_tree = loc.get('has_tree', False)
                    is_plantable = loc.get('is_plantable', False)
                    pollution = loc.get('pollution', 50)
                    score = loc.get('score', 0)
                    temperature = loc.get('temperature', 25)
                    scan_type = loc.get('scan_type', 'wide')
                    refine_level = loc.get('refine_level', 0)
                    
                    color = MapColors.get_land_color(land_type, is_plantable, has_tree)
                    radius = MapColors.get_radius(scan_type, pollution, refine_level)
                    popup_text = MapColors.get_popup_text(loc)
                    
                    locations_data.append({'lat': lat, 'lon': lon, 'color': color, 'radius': radius, 'popup': popup_text})
        else:
            locations_data = self._prepare_locations_data()
        
        self.update_map_points(locations_data)
    
    def show_fine_locations_only(self):
        if not self.map_initialized:
            self.parent.after(1000, self.show_fine_locations_only)
            return
        
        try:
            parent = self.parent
            while parent:
                if hasattr(parent, 'current_points') and hasattr(parent, 'prepare_locations_data_for_map'):
                    if parent.current_points:
                        non_plantable = ['building', 'road', 'water', 'industrial', 'commercial', 'desert', 'barren', 'tundra']
                        plantable = []
                        for p in parent.current_points:
                            is_plantable = p.get('is_plantable', False) or (p.get('land_type', '').lower() not in non_plantable) or p.get('score', 0) > 30
                            if p.get('has_tree', False) or p.get('land_type') in ['loading', 'error']:
                                is_plantable = False
                            if is_plantable:
                                plantable.append(p)
                        
                        if plantable:
                            self.update_map_points(parent.prepare_locations_data_for_map(plantable))
                        return
                parent = getattr(parent, 'master', None)
        except Exception as e:
            print(f"Error: {e}")
        
        locations_data = []
        for loc in self.fine_locations:
            if isinstance(loc, dict) and 'location' in loc:
                is_plantable = loc.get('is_plantable', False) or loc.get('land_type', '') not in ['building', 'road', 'water', 'industrial', 'commercial']
                if is_plantable:
                    lat, lon = loc['location']
                    land_type = loc.get('land_type', 'empty')
                    has_tree = loc.get('has_tree', False)
                    pollution = loc.get('pollution', 50)
                    score = loc.get('score', 0)
                    temperature = loc.get('temperature', 25)
                    scan_type = loc.get('scan_type', 'fine')
                    refine_level = loc.get('refine_level', 0)
                    
                    color = MapColors.get_land_color(land_type, is_plantable, has_tree)
                    radius = MapColors.get_radius(scan_type, pollution, refine_level)
                    popup_text = MapColors.get_popup_text(loc)
                    locations_data.append({'lat': lat, 'lon': lon, 'color': color, 'radius': radius, 'popup': popup_text})
        
        self.update_map_points(locations_data)
    
    def _init_qt(self):
        if self.qt_app is None:
            self.qt_app = QApplication.instance()
            if self.qt_app is None:
                self.qt_app = QApplication(sys.argv)
    
    def _embed_qt_in_tk(self):
        for w in self.map_frame.winfo_children():
            w.destroy()
        
        self.qt_container = ttk.Frame(self.map_frame)
        self.qt_container.pack(fill=tk.BOTH, expand=True)
        hwnd = self.qt_container.winfo_id()
        
        self._init_qt()
        
        self.qt_widget = QWidget()
        self.qt_widget.setParent(None)
        
        layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.qt_widget.setLayout(layout)
        
        self.channel = QWebChannel()
        self.web_view.page().setWebChannel(self.channel)
        self.channel.registerObject("bridge", self._bridge)
        self.qt_widget.show()
        
        if os.name == 'nt':
            try:
                import win32gui
                import win32con
                qt_hwnd = int(self.qt_widget.winId())
                win32gui.SetParent(qt_hwnd, hwnd)
                style = win32gui.GetWindowLong(qt_hwnd, win32con.GWL_STYLE)
                style = style & ~win32con.WS_POPUP | win32con.WS_CHILD
                win32gui.SetWindowLong(qt_hwnd, win32con.GWL_STYLE, style)
                win32gui.MoveWindow(qt_hwnd, 0, 0, self.qt_container.winfo_width(), self.qt_container.winfo_height(), True)
                
                def resize_handler(e):
                    win32gui.MoveWindow(qt_hwnd, 0, 0, self.qt_container.winfo_width(), self.qt_container.winfo_height(), True)
                    if self.web_view and self.map_initialized:
                        self.web_view.page().runJavaScript("var m=Object.values(window).find(o=>o instanceof L.Map);if(m){setTimeout(function(){m.invalidateSize();},100);}")
                
                self.qt_container.bind('<Configure>', resize_handler)
            except ImportError:
                self.web_view.show()
        
        self.web_view.page().consoleMessage = lambda msg: None
    
    def init_map(self):
        center_lat, center_lon = 31.0364, 31.3807
        
        if self.graph and hasattr(self.graph, 'center_lat') and self.graph.center_lat:
            center_lat, center_lon = self.graph.center_lat, self.graph.center_lon
        elif self.graph and hasattr(self.graph, 'nodes') and self.graph.nodes:
            first = next(iter(self.graph.nodes.values()))
            center_lat, center_lon = first.get_location()
        
        self.current_center_lat, self.current_center_lon = center_lat, center_lon
        
        self.map = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles='CartoDB positron')
        
        plugins.Draw(export=True, draw_options={'polygon': True, 'circle': False, 'rectangle': False, 'polyline': False, 'marker': False, 'circlemarker': False},
                     edit_options={'edit': False, 'remove': False}).add_to(self.map)
        
        self.map.get_root().html.add_child(folium.Element('<div id="points-layer" style="display:none;"></div>'))
        
        js = """
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script>
        (function(){
            var map=null, pointLayer=null;
            function sendPolygon(p){
                if(typeof qt!=='undefined'&&qt.webChannelTransport){
                    new QWebChannel(qt.webChannelTransport,function(c){
                        var b=c.objects.bridge;
                        if(b) b.receive_polygon(p);
                    });
                }
            }
            function setup(){
                map=Object.values(window).find(o=>o instanceof L.Map);
                if(!map){setTimeout(setup,500);return;}
                pointLayer=L.layerGroup().addTo(map);
                map.on('draw:created',function(e){
                    var l=e.layer;
                    if(l instanceof L.Polygon){
                        var pts=[];
                        l.getLatLngs()[0].forEach(function(c){pts.push([c.lat,c.lng]);});
                        sendPolygon(pts);
                    }
                });
                setTimeout(function(){if(map)map.invalidateSize();},500);
            }
            if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',setup);
            else setup();
            window.updatePoints=function(d){
                if(pointLayer)pointLayer.clearLayers();
                if(!map)return;
                if(!pointLayer)pointLayer=L.layerGroup().addTo(map);
                d.forEach(function(p){
                    var m=L.circleMarker([p.lat,p.lon],{radius:p.radius||6,color:p.color||'#3388ff',fillColor:p.color||'#3388ff',fillOpacity:0.7,weight:2});
                    m.bindPopup(p.popup);
                    m.addTo(pointLayer);
                });
            };
            window.appendPoints=function(d){
                if(!map)return;
                if(!pointLayer)pointLayer=L.layerGroup().addTo(map);
                d.forEach(function(p){
                    var m=L.circleMarker([p.lat,p.lon],{radius:p.radius||6,color:p.color||'#3388ff',fillColor:p.color||'#3388ff',fillOpacity:0.7,weight:2});
                    m.bindPopup(p.popup);
                    m.addTo(pointLayer);
                });
            };
            window.clearPoints=function(){if(pointLayer)pointLayer.clearLayers();};
        })();
        </script>
        """
        self.map.get_root().html.add_child(folium.Element(js))
        
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8')
        self.map.save(self.temp_file.name)
        self.temp_file.close()
        
        self._embed_qt_in_tk()
        self.web_view.setUrl(QUrl.fromLocalFile(self.temp_file.name))
        self.map_initialized = True
    
    def update_map_center(self, lat, lon):
        self.current_center_lat, self.current_center_lon = lat, lon
        if self.web_view and self.map_initialized:
            self.web_view.page().runJavaScript(f"var m=Object.values(window).find(o=>o instanceof L.Map);if(m){{m.setView([{lat},{lon}],13);setTimeout(function(){{m.invalidateSize();}},100);}}")
    
    def update_map_points(self, locations_data, append=False):
        if not self.web_view or not self.map_initialized:
            return
        if not locations_data:
            return
        
        for p in locations_data:
            if 'icon' in p and p['icon'] and '🌳' not in p.get('popup', ''):
                p['popup'] = f"{p['icon']} {p['popup']}"
        
        data = json.dumps(locations_data)
        if append:
            self.web_view.page().runJavaScript(f"window.appendPoints({data});")
        else:
            self.web_view.page().runJavaScript(f"window.updatePoints({data});")
    
    def update_heatmap(self, heat_data):
        if not self.web_view or not self.map_initialized or not heat_data:
            return
        self.web_view.page().runJavaScript(f"window.updateHeatmap({json.dumps(heat_data)});")
    
    def clear_points(self):
        if self.web_view and self.map_initialized:
            self.web_view.page().runJavaScript("window.clearPoints();")
    
    def show_map(self):
        try:
            parent = self.parent
            while parent:
                if hasattr(parent, 'current_points') and hasattr(parent, 'prepare_locations_data_for_map'):
                    if parent.current_points:
                        self.update_map_points(parent.prepare_locations_data_for_map(parent.current_points))
                        return
                parent = getattr(parent, 'master', None)
        except Exception as e:
            print(f"Error: {e}")
        
        if self.wide_locations or self.fine_locations:
            self.show_all_locations()
        elif self.graph and hasattr(self.graph, 'nodes') and self.graph.nodes:
            d = self._prepare_locations_data()
            if d:
                self.update_map_points(d)
    
    def show_locations(self):
        if not self.map_initialized:
            self.parent.after(1000, self.show_locations)
            return
        
        non_plantable = ['building', 'road', 'water', 'industrial', 'commercial', 'desert', 'barren', 'tundra']
        try:
            parent = self.parent
            while parent:
                if hasattr(parent, 'current_points') and hasattr(parent, 'prepare_locations_data_for_map'):
                    if parent.current_points:
                        plantable = []
                        for p in parent.current_points:
                            is_plantable = p.get('is_plantable', False) or (p.get('land_type', '').lower() not in non_plantable) or p.get('score', 0) > 30
                            if p.get('has_tree', False) or p.get('land_type') in ['loading', 'error']:
                                is_plantable = False
                            if is_plantable:
                                plantable.append(p)
                        if plantable:
                            self.update_map_points(parent.prepare_locations_data_for_map(plantable))
                        return
                parent = getattr(parent, 'master', None)
        except Exception as e:
            print(f"Error: {e}")
        
        if self.graph and hasattr(self.graph, 'nodes') and self.graph.nodes:
            plantable = []
            for nid, loc in self.graph.nodes.items():
                if loc.is_plantable() and not loc.has_tree:
                    lat, lon = loc.get_location()
                    plantable.append({'lat': lat, 'lon': lon, 'color': MapColors.PLANTABLE_COLOR, 'radius': 6,
                                     'popup': f"<b>Plantable</b><br>Score: {loc.score:.1f}<br>Type: {loc.land_type}"})
            if plantable:
                self.update_map_points(plantable)
    
    def _prepare_locations_data(self):
        if not self.graph or not hasattr(self.graph, 'nodes') or len(self.graph.nodes) == 0:
            return []
        
        data = []
        for nid, loc in self.graph.nodes.items():
            lat, lon = loc.get_location()
            color = MapColors.get_land_color(loc.land_type, loc.is_plantable(), loc.has_tree)
            radius = MapColors.get_radius('wide', loc.pollution, 0)
            icon = "🌳" if loc.has_tree else ""
            popup = MapColors.get_popup_text({'land_type': loc.land_type, 'is_plantable': loc.is_plantable(),
                                              'pollution': loc.pollution, 'temperature': loc.temperature,
                                              'score': loc.score, 'has_tree': loc.has_tree})
            if icon:
                popup = f"{icon} {popup}"
            data.append({'lat': lat, 'lon': lon, 'color': color, 'radius': radius, 'popup': popup})
        return data
    
    def show_trees(self):
        if not self.map_initialized:
            self.parent.after(1000, self.show_trees)
            return
        
        try:
            parent = self.parent
            while parent:
                if hasattr(parent, 'current_points') and hasattr(parent, 'prepare_locations_data_for_map'):
                    if parent.current_points:
                        trees = []
                        for p in parent.current_points:
                            if p.get('has_tree', False):
                                trees.append({'lat': p['location'][0], 'lon': p['location'][1],
                                            'color': '#2ecc71', 'radius': 12, 'icon': '🌳',
                                            'popup': f"🌳 Tree<br>Score: {p.get('score',0):.1f}<br>Land Type: {p.get('land_type','unknown')}"})
                        if trees:
                            self.update_map_points(trees)
                        else:
                            self.web_view.page().runJavaScript("var m=Object.values(window).find(o=>o instanceof L.Map);if(m){L.popup().setLatLng(m.getCenter()).setContent('🌳 No trees yet. Run Algorithm first!').openOn(m);}")
                        return
                parent = getattr(parent, 'master', None)
        except Exception as e:
            print(f"Error: {e}")
        
        if self.graph and hasattr(self.graph, 'nodes') and self.graph.nodes:
            trees = []
            for nid, loc in self.graph.nodes.items():
                if loc.has_tree:
                    lat, lon = loc.get_location()
                    trees.append({'lat': lat, 'lon': lon, 'color': '#2ecc71', 'radius': 12, 'icon': '🌳',
                                 'popup': f"🌳 Tree at {nid}<br>Score: {loc.score:.1f}"})
            if trees:
                self.update_map_points(trees)
    
    def show_heatmap(self):
        if not self.map_initialized:
            self.parent.after(1000, self.show_heatmap)
            return
        
        if not self.graph or not hasattr(self.graph, 'nodes'):
            return
        
        heat = []
        for nid, loc in self.graph.nodes.items():
            lat, lon = loc.get_location()
            heat.append([lat, lon, loc.pollution])
        self.update_heatmap(heat)
    
    def __del__(self):
        if self.temp_file and os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except:
                pass