import { Component, OnInit, ViewChild, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { AgmMap, AgmInfoWindow } from '@agm/core';
import { Router } from '@angular/router';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Response } from 'src/app/shared/models/response';
import { Options as SliderOptions } from '@angular-slider/ngx-slider';

@Component({
  selector: 'app-map-result',
  templateUrl: './map-result.component.html',
  styleUrls: ['./map-result.component.css']
})
export class MapResultComponent implements OnInit {

  constructor(
   private router: Router,
   private plotService: PlotService,
  ) { }

  mapBuilder: MapBuilder;
  results: any[];
  _results: any[]; // contains all results including results that are hidden
  lowestScale: number;
  highestScale: number;
  averageScale: number;
  categories: Map<string, any> = new Map();
  public sliderOptions: SliderOptions;
  public showSlider = false;
  averageLong: number;
  averageLat: number;
  showNullValues = true;
  hasNullValues = false;
  colorSignificantDigits: number;
  labelSignificantDigits: number;
  colorFieldEqualsLabelField = false;

  @ViewChild('map') map: AgmMap;
  @ViewChild('infoWindow') infoWindow: AgmInfoWindow;

  ngOnInit(): void {
    this.mapBuilder = Object.assign(new MapBuilder(), JSON.parse(localStorage.getItem('mapBuilder')));
    this.setColorFieldEqualsLabelField();
    if (this.mapBuilder.isCoreType) {
      this.plotService.getStaticMap(this.mapBuilder).subscribe(res => this.initMap(res));
    } else {
      this.plotService.testDynamicMap(this.mapBuilder.brickId, this.mapBuilder)
        .subscribe(data => this.initMap(data))
      // this.plotService.getDynamicMap(this.mapBuilder).subscribe((res: Response<any>) => this.initMap(res.results));
    }
  }

  initMap(results) {
    this.setMapCenter(results);
    if (this.mapBuilder.colorField.scalar_type === 'float') {
      this.colorSignificantDigits = this.calculateSignificantDigits(results, 'color');
    }
    if (this.mapBuilder.labelField.scalar_type === 'float') {
      this.labelSignificantDigits = this.calculateSignificantDigits(results,'label_text');
    }
    if (this.mapBuilder.colorField) {
      if (this.mapBuilder.colorFieldScalarType === 'term') {
        this.plotCategoryColorMarkers(results);
      } else {
        this.plotNumericColorMarkers(results);
      }
    } else {
      this.results = results.map(result => ({...result, scale: 'FF0000', hover: false})); // TODO: handle extra object fields in subscription
      this._results = this.results;
    }
  }

  setColorFieldEqualsLabelField() {
    const {colorField, labelField} = this.mapBuilder
    if (this.mapBuilder.isCoreType) {
      this.colorFieldEqualsLabelField = colorField.term_id === labelField.term_id;
      return;
    }
    if (labelField.data_variable === colorField.data_variable) {
      this.colorFieldEqualsLabelField = true;
    }
    this.colorFieldEqualsLabelField = colorField.dimension === labelField.dimension && colorField.dimension_variable === labelField.dimension_variable;
  }

  setMapCenter(data) {
    this.averageLat = data.reduce((a, d) => a + d.latitude, 0) / data.length;
    this.averageLong = data.reduce((a, d) => a + d.longitude, 0) / data.length;
  }

  plotCategoryColorMarkers(data: any[]) {
    const field = this.mapBuilder.colorField.name;
    this.results = data.map(result => {
      if (this.categories.has(result.color)) {
        return {...result, scale: this.categories.get(result.color).color}
      }
      const newColor = this.generateRandomColor();
      this.categories.set(result.color, {color: newColor, display: true});
      return {...result, scale: newColor, hover: false};
    });
    this._results = this.results;
  }

  markerShouldBeDisplayed(marker) {
    if (this.mapBuilder.colorFieldScalarType === 'term') {
      return this.categories.get(marker[this.mapBuilder.colorField.name]).display
    }
    if (this.mapBuilder.colorField) {
      return !this.hasNullValues || (marker.color !== null || this.showNullValues)
    }
    return true;
  }

  generateRandomColor(): string {
    return Array.from({length: 3}, () => {
      return (Math.floor(Math.random() * 105) + 150)
        .toString(16)
        .toUpperCase()
        .padStart(2, '0');
      })
      .join('');
  }

  plotNumericColorMarkers(data: any[]) {
    const field = this.mapBuilder.colorField.name;

    this.lowestScale = +Math.min.apply(null, data.map(d => d.color)).toFixed(this.colorSignificantDigits);
    this.highestScale = +Math.max.apply(null, data.map(d => d.color)).toFixed(this.colorSignificantDigits);
    this.averageScale = data.reduce((a, d) => a + d.color, 0) / data.length;

    this.results = data.map(result => {
      const item: any = {
        scale: this.calculateScale(result),
        hover: false,
        latitude: result.latitude,
        longitude: result.longitude
      }
      try {
        if (this.mapBuilder.colorFieldScalarType !== 'term' && this.colorSignificantDigits !== undefined) {
          item.color = +result.color.toFixed(this.colorSignificantDigits)
        } else {
          item.color = result.color;
        }
      } catch(e) {
        item.color = null;
      }
      try {
        if (this.mapBuilder.labelField.scalar_type === 'float' && this.labelSignificantDigits !== undefined) {
          const numString = parseFloat(result.label_text).toFixed(this.labelSignificantDigits);
          item.label_text = isNaN(parseFloat(result.label_text)) ? 'null' : numString;
        } else {
          item.label_text = result.label_text;
        }
      } catch(e) {
        item.label_text = 'Null';
      }
      return item;
  })
    this._results = this.results;
    this.setSliderOptions();
  }

  calculateSignificantDigits(data, field): number {
    let smallest = Infinity;
    data.sort((a, b) => a.color - b.color).forEach((d, i) => {
      if (i === 0) return;
      const difference = d.color - data[i - 1].color;
      if (difference < smallest && difference !== 0) {
        smallest = difference;
      }
    });
    if (/[0-9]e\-[0-9]/.test(smallest.toString())) {
      // if number converted to string is exponent like 1e-9 we just need to use the exponent value
      return +smallest.toString().split('-')[1];
    }
    let idx = 0;
    const string = smallest.toString().split('.')[1];
    if (!string) return 0;
    while (string[idx] === '0') {
      idx++;
    }
    return idx;
  }

  calculateScale(result: any): string {
    // calculate hex color scale based on numeric value

    const totalRange = this.highestScale - this.lowestScale;
    let red = 255, blue = 255;
    if (result.color === null) { 
      this.hasNullValues = true; // TODO: this is a side effect
      return 'AAA';
     }
    
    if (result.color < this.averageScale) {
      blue = 255;
      const difference = result.color - this.lowestScale;
      red = Math.min(Math.floor((difference / (totalRange / 2)) * 255), 255);
    }

    if (result.color > this.averageScale) {
      red = 255;
      const difference = this.highestScale - result.color;
      blue = Math.min(Math.floor((difference / (totalRange/2)) * 255), 255);
    }
    return `${red.toString(16).toUpperCase().padStart(2, '0')}00${blue.toString(16).toUpperCase().padStart(2, '0')}`;
  }

  setSliderOptions() {
    this.sliderOptions = {
      floor: this.lowestScale,
      ceil: this.highestScale,
      step: (this.highestScale - this.lowestScale) / this.results.length,
      getPointerColor: () => '#00489B',
      selectionBarGradient: {
        from: '#0000FF',
        to: '#FF0000'
      }
    }
    this.showSlider = true;
  }

  filterMarkersWithSlider(event) {
    const field = this.mapBuilder.colorField.name;
    this.results = this._results.filter(result => {
      if (result.color === null) return true;
      return result.color > event.value && result.color < event.highValue;
    })
  }

  getIconUrl(scale) {
    return `http://chart.googleapis.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|${scale}|000000`;
  }

  navigateBack() {
    if (this.mapBuilder.isCoreType) {
      this.router.navigate(['/plot/options'], {
        queryParams: { coreType: this.mapBuilder.query.queryMatch.dataType }
      })
    } else {
      this.router.navigate([`/plot/options/${this.mapBuilder.brickId}`]);
    }
  }

  onMouseOver(infoWindow: AgmInfoWindow) {
    if (this.mapBuilder.labelField) {
      infoWindow.open();
    }
  }

  onMouseOut(infoWindow: AgmInfoWindow) {
    infoWindow.close();
  }

}
