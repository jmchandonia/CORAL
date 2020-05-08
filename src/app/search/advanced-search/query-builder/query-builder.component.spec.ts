import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { QueryBuilderComponent } from './query-builder.component';
import { Select2Module } from 'ng2-select2';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { MockComponent } from 'ng-mocks';
import { PropertyParamsComponent } from './property-params/property-params.component';

describe('QueryBuilderComponent', () => {
  let spectator: Spectator<QueryBuilderComponent>;
  const createComponent = createComponentFactory({
    component: QueryBuilderComponent,
    imports: [
      Select2Module,
      HttpClientModule,
      RouterModule.forRoot([])
    ],
    entryComponents: [
      MockComponent(PropertyParamsComponent)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
