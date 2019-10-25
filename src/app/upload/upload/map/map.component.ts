import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, DimensionVariable, TypedProperty } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements OnInit {

  brick: Brick;
  dimVars: DimensionVariable[] = [];
  testArray = [];

  constructor(private uploadService: UploadService) { }

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.brick.dimensions.forEach(dim => {
      this.dimVars = [...this.dimVars, ...dim.variables];
    });
    this.testArray = [...Array(this.dimVars.length)].map(() => { return Math.floor(Math.random() * 10) % 2 === 0});
    console.log('STUPID BOOLEAN ARRAY', this.testArray);
  }

  testMap() {
    this.uploadService.mapDimVarToCoreTypes(this.dimVars[0])
      .subscribe((result: any) => {
        console.log('RESULT', result);
      });
  }

}
