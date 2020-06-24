import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { PropertyParamsComponent } from './property-params.component';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { RouterModule } from '@angular/router';
import { QueryParam } from 'src/app/shared/models/QueryBuilder';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { NgSelectModule } from '@ng-select/ng-select';

describe('PropertyParamsComponent', () => {

  let spectator: Spectator<PropertyParamsComponent>;
  const createComponent = createComponentFactory({
    component: PropertyParamsComponent,
    imports: [
      FormsModule,
      HttpClientModule,
      RouterModule.forRoot([]),
      NgSelectModule
    ],
    providers: [
      mockProvider(QueryBuilderService, {
        getAttributes: (dataType: string) => [{id: '0', text: 'NDArray'}]
      })
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      queryParam: new QueryParam()
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
