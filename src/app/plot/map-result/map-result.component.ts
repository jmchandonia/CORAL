import { Component, OnInit } from '@angular/core';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';

@Component({
  selector: 'app-map-result',
  templateUrl: './map-result.component.html',
  styleUrls: ['./map-result.component.css']
})
export class MapResultComponent implements OnInit {

  constructor(
   private queryBuilder: QueryBuilderService
  ) { }

  private mapBuilder: MapBuilder;
  results: any[];
  averageLat: number;
  averageLng: number;

  ngOnInit(): void {
    this.mapBuilder = JSON.parse(localStorage.getItem('mapBuilder'));
    console.log('MAP BUILDer', this.mapBuilder)
    this.queryBuilder.getMapSearchResults(this.mapBuilder.query)
      .subscribe(res => {
        this.averageLat = res.data.reduce((a, {latitude}) => a + latitude, 0) / res.data.length;
        this.averageLng = res.data.reduce((a, {longitude}) => a + longitude, 0) / res.data.length;
        console.log('average lat', this.averageLat);
        console.log("DATA", res);
        this.results = res.data;
      })
  } 

}
